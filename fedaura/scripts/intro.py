"""The minimal agent loop, using the same local product catalog as the UI."""
import json
import sys
import urllib.request
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI

env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
client = OpenAI(base_url=env["LLM_BASE_URL"], api_key=env["LLM_API_KEY"])
tools = [{"type": "function", "function": {
    "name": "product_info", "description": "Look up Fedaura's fictional mortgage product catalog.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}}]
messages = [
    {"role": "system", "content": "Use product_info before answering product questions. Summarize three products in under 100 words. Rates are synthetic demo data."},
    {"role": "user", "content": "What mortgage products does Fedaura offer?"},
]

for step in range(1, 5):
    reply = client.chat.completions.create(model=env["LLM_MODEL"], messages=messages,
                                           tools=tools, temperature=0, reasoning_effort="none")
    message = reply.choices[0].message
    messages.append(message.model_dump(exclude_none=True))
    if not message.tool_calls:
        print("ANSWER:", message.content)
        break
    for call in message.tool_calls:
        if call.function.name != "product_info":
            raise RuntimeError("Unknown tool")
        print(f"[step {step}] tool: product_info", flush=True)
        with urllib.request.urlopen("http://127.0.0.1:8100/api/public/products", timeout=5) as response:
            catalog = json.load(response)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(catalog)})
else:
    raise SystemExit("Agent reached its step limit")
