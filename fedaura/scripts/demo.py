"""Local Fedaura lifecycle. Owns only its PID files and Compose project."""
import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import psutil
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
RUNTIME = ROOT / "runtime"
PYTHON = ROOT / ".venv/bin/python"
PNPM = ROOT / ".tools/node_modules/.bin/pnpm"
COMPOSE = [str(ROOT / ".venv/bin/podman-compose"), "-f", str(ROOT / "compose.yml"), "-p", "fedaura-local"]


def environment(stage=None):
    env = os.environ.copy()
    env.update({key: value or "" for key, value in dotenv_values(ROOT / ".env").items()})
    env["FEDAURA_STAGE"] = stage or current_stage()
    env["FEDAURA_RUNTIME_DIR"] = str(RUNTIME)
    env["PYTHONUNBUFFERED"] = "1"
    env["LANGSMITH_TRACING"] = "false"
    env["LANGCHAIN_TRACING_V2"] = "false"
    return env


def current_stage():
    path = RUNTIME / "stage"
    return path.read_text().strip() if path.exists() else "assistant"


def run(command, cwd=ROOT, env=None):
    subprocess.run([str(x) for x in command], cwd=cwd, env=env or environment(), check=True)


def managed(name):
    path = RUNTIME / f"{name}.pid.json"
    if not path.exists():
        return None
    try:
        info = json.loads(path.read_text())
        process = psutil.Process(info["pid"])
        if abs(process.create_time() - info["created"]) < .01 and process.status() != psutil.STATUS_ZOMBIE:
            return process
    except (ValueError, KeyError, psutil.Error):
        pass
    return None


def stop(name):
    process = managed(name)
    if process:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except psutil.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    (RUNTIME / f"{name}.pid.json").unlink(missing_ok=True)


def start(name, command, cwd=APP, stage=None):
    if managed(name):
        return
    with (RUNTIME / f"{name}.log").open("a") as output:
        process = subprocess.Popen([str(x) for x in command], cwd=cwd, env=environment(stage),
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    info = {"pid": process.pid, "created": psutil.Process(process.pid).create_time()}
    (RUNTIME / f"{name}.pid.json").write_text(json.dumps(info))


def get_json(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        return json.load(response)


def wait_for(description, check, seconds=90):
    print(f"Waiting for {description}...", flush=True)
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        for service, marker in (("api", "Fedaura API"), ("ui", "Fedaura UI"), ("mcp", "MCP risk service")):
            if description == marker and (RUNTIME / f"{service}.pid.json").exists() and not managed(service):
                raise RuntimeError(f"{service} exited. Read {RUNTIME / (service + '.log')}")
        try:
            result = check()
            if result is not False:
                return result
        except Exception as error:
            last = error
        time.sleep(1)
    raise RuntimeError(f"{description} did not become ready: {last}. See {RUNTIME} logs.")


def check_database():
    import psycopg
    url = environment()["DATABASE_URL"].replace("+asyncpg", "")
    with psycopg.connect(url, connect_timeout=3) as conn:
        return conn.execute("SELECT 1").fetchone()


def storage():
    import boto3
    from botocore.config import Config
    env = environment()
    return boto3.client("s3", endpoint_url=env["S3_ENDPOINT"],
                        aws_access_key_id=env["S3_ACCESS_KEY"],
                        aws_secret_access_key=env["S3_SECRET_KEY"],
                        region_name=env["S3_REGION"],
                        config=Config(connect_timeout=3, read_timeout=5,
                                      retries={"max_attempts": 0}, s3={"addressing_style": "path"}))


def up(stage):
    if not (ROOT / ".env").exists():
        raise RuntimeError("Run demo.sh setup first, or copy .env.example to .env")
    RUNTIME.mkdir(exist_ok=True)
    env = environment(stage)
    if not env["LLM_BASE_URL"].startswith(("http://127.0.0.1:", "http://localhost:")):
        raise RuntimeError("This launcher is for local inference. Switch to your existing cluster app separately.")
    try:
        get_json("http://127.0.0.1:11434/api/tags")
    except Exception:
        start("ollama", ["ollama", "serve"], cwd=ROOT)
    tags = wait_for("Ollama", lambda: get_json("http://127.0.0.1:11434/api/tags"))
    if env["LLM_MODEL"] not in {model["name"] for model in tags.get("models", [])}:
        raise RuntimeError(f"Pull {env['LLM_MODEL']} with ollama before running the demo")
    run(COMPOSE + ["up", "-d"])
    wait_for("PostgreSQL", check_database)
    wait_for("S4 object storage", lambda: storage().list_buckets(), seconds=150)
    client = storage()
    if env["S3_BUCKET"] not in {bucket["Name"] for bucket in client.list_buckets()["Buckets"]}:
        client.create_bucket(Bucket=env["S3_BUCKET"])
    run([PYTHON, "-m", "alembic", "upgrade", "head"], cwd=APP / "packages/db", env=env)
    # Always rebuild the API process when changing stages so cached agent graphs
    # and MCP discovery cannot carry over from the previous stage.
    stop("api")
    if stage == "mcp":
        start("mcp", [PYTHON, "-m", "src.mcp_server"], cwd=APP / "packages/api", stage=stage)
        wait_for("MCP risk service", lambda: get_json("http://127.0.0.1:8181/health"))
    else:
        stop("mcp")
    (RUNTIME / "stage").write_text(stage)
    start("api", [PYTHON, "-m", "uvicorn", "src.main:app", "--host", "127.0.0.1", "--port", "8100"],
          cwd=APP / "packages/api", stage=stage)
    wait_for("Fedaura API", lambda: get_json("http://127.0.0.1:8100/health/"), seconds=150)
    import psycopg
    with psycopg.connect(env["DATABASE_URL"].replace("+asyncpg", "")) as conn:
        if not conn.execute("SELECT COUNT(*) FROM demo_data_manifest").fetchone()[0]:
            raise RuntimeError("The API is healthy but synthetic data seeding failed; inspect api.log")
    if stage == "mcp":
        # A healthy server is insufficient: fail if API-side discovery did not load its tools.
        log = (RUNTIME / "api.log").read_text()
        latest = log.rsplit("Started server process", 1)[-1]
        if "MCP client initialized: 6 tools" not in latest:
            raise RuntimeError("API started without the six MCP tools; inspect api.log")
    start("ui", [PNPM, "--filter", "@mortgage-ai/ui", "exec", "vite"], stage=stage)
    wait_for("Fedaura UI", lambda: urllib.request.urlopen("http://127.0.0.1:3100", timeout=3).close())
    print(f"\nFedaura stage: {stage}\nUI: http://127.0.0.1:3100\nAPI: http://127.0.0.1:8100/docs\nLogs: {RUNTIME}\n", flush=True)


def status():
    print(f"Stage: {current_stage()}")
    for name in ("api", "ui", "mcp", "ollama"):
        process = managed(name)
        print(f"{name}: {'running (owned PID '+str(process.pid)+')' if process else 'no process owned by this launcher'}")
    try:
        get_json("http://127.0.0.1:11434/api/tags")
        print("Ollama endpoint: reachable")
    except Exception as error:
        print(f"Ollama endpoint: {error}")
    for name, url in (("API", "http://127.0.0.1:8100/health/"),
                      ("MCP", "http://127.0.0.1:8181/health")):
        try:
            if name == "MCP" and current_stage() == "assistant":
                print("MCP: intentionally disabled in assistant stage")
                continue
            print(f"{name} health: {get_json(url)}")
        except Exception as error:
            print(f"{name} health: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["up", "stage", "down", "status", "logs", "check", "chat", "intro", "mcp", "test"])
    parser.add_argument("argument", nargs="?")
    args = parser.parse_args()
    if args.command in {"up", "stage"}:
        stage = args.argument or "assistant"
        if stage not in {"assistant", "mcp"}:
            parser.error("stage must be assistant or mcp")
        up(stage)
    elif args.command == "down":
        for name in ("ui", "api", "mcp", "ollama"):
            stop(name)
        run(COMPOSE + ["stop"])
        print("Fedaura stopped. Synthetic database and storage volumes retained.")
    elif args.command == "status":
        status()
    elif args.command == "test":
        test_env = environment()
        test_env.pop("FEDAURA_RUNTIME_DIR", None)
        run([PYTHON, "-m", "pytest", "tests/test_mcp_tools.py", "-q"], cwd=APP / "packages/api", env=test_env)
    elif args.command == "logs":
        name = args.argument or "api"
        if name not in {"api", "ui", "mcp", "ollama"}:
            parser.error("log service must be api, ui, mcp or ollama")
        os.execvp("tail", ["tail", "-n", "40", "-f", str(RUNTIME / f"{name}.log")])
    elif args.command in {"check", "chat", "intro", "mcp"}:
        filename = {"check": "check.py", "chat": "chat.py", "intro": "intro.py", "mcp": "inspect_mcp.py"}[args.command]
        run([PYTHON, ROOT / "scripts" / filename] + ([args.argument] if args.argument else []))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Fedaura: {error}", file=sys.stderr)
        sys.exit(1)
