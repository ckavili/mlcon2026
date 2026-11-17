"""Rehearse the same real WebSocket endpoints used by the UI."""
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import websockets

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "products": ("/api/chat", {"product_info"}),
    "affordability": ("/api/chat", {"affordability_calc"}),
    "risk": ("/api/underwriter/chat", {"calculate_dti", "calculate_ltv", "evaluate_credit_risk"}),
    "queue": ("/api/underwriter/chat", {"uw_queue_view"}),
}


async def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "products"
    if scenario not in SCENARIOS:
        raise SystemExit("Choose: " + ", ".join(SCENARIOS))
    route, required = SCENARIOS[scenario]
    prompt = (ROOT / "prompts" / f"{scenario}.txt").read_text().strip()
    print(f"Scenario: {scenario}\nPrompt: {prompt}", flush=True)
    events = []
    observed = set()
    started = time.monotonic()
    # Each rehearsal must be fresh: authenticated chats otherwise reuse durable
    # threads and can correctly answer from earlier tool results without a new call.
    user_id = "fedaura-rehearsal-" + uuid.uuid4().hex
    route += "?dev_user_id=" + user_id
    base = os.environ.get("FEDAURA_CHAT_BASE_URL", "ws://127.0.0.1:8100")
    async with websockets.connect(base + route, open_timeout=15) as connection:
        await connection.send(json.dumps({"type": "message", "content": prompt}))
        async with asyncio.timeout(240):
            async for raw in connection:
                event = json.loads(raw)
                events.append(event)
                if event["type"] == "tool_start":
                    observed.add(event["tool_name"])
                    print(f"  tool → {event['tool_name']}", flush=True)
                if event["type"] == "error":
                    raise RuntimeError(event.get("content"))
                if event["type"] == "done":
                    print("\n" + event.get("content", ""), flush=True)
                    break
    missing = required - observed
    result = {"scenario": scenario, "time": datetime.now(timezone.utc).isoformat(),
              "seconds": round(time.monotonic() - started, 1), "prompt": prompt,
              "required_tools": sorted(required), "observed_tools": sorted(observed),
              "tool_check_passed": not missing, "events": events}
    (ROOT / "runtime" / f"chat-{scenario}.json").write_text(json.dumps(result, indent=2) + "\n")
    if not events or events[-1]["type"] != "done":
        raise RuntimeError("Chat closed without completing")
    if missing:
        raise RuntimeError(f"Required tools were not called: {sorted(missing)}")
    print(f"\nPASS: required tool calls observed; {result['seconds']}s. Review the answer separately.")


asyncio.run(main())
