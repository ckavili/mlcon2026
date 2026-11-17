"""Check local infrastructure, seeded data and MCP without invoking the LLM."""
import asyncio
import json
import sys
import urllib.request
from pathlib import Path

import psycopg
import boto3
from dotenv import dotenv_values
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parents[1]
ENV = dotenv_values(ROOT / ".env")


def get(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


async def main():
    assert get("http://127.0.0.1:8100/health/")
    products = get("http://127.0.0.1:8100/api/public/products")
    assert any(product["id"] == "conventional_30" for product in products)
    with urllib.request.urlopen("http://127.0.0.1:3100", timeout=5) as response:
        assert response.status == 200
    boto3.client("s3", endpoint_url=ENV["S3_ENDPOINT"],
                 aws_access_key_id=ENV["S3_ACCESS_KEY"],
                 aws_secret_access_key=ENV["S3_SECRET_KEY"],
                 region_name=ENV["S3_REGION"]).head_bucket(Bucket=ENV["S3_BUCKET"])
    url = ENV["DATABASE_URL"].replace("+asyncpg", "")
    with psycopg.connect(url) as conn:
        count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        manifest = conn.execute("SELECT summary FROM demo_data_manifest ORDER BY id DESC LIMIT 1").fetchone()
        assert count > 0 and manifest, "Synthetic data was not seeded successfully"
        print(f"PASS: UI, API, product catalog and {count} seeded applications")
    stage = (ROOT / "runtime/stage").read_text().strip()
    if stage != "mcp":
        print("Assistant stage: external risk MCP intentionally not enabled")
        return
    async with streamablehttp_client(ENV["MCP_RISK_SERVER_URL"]) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = {tool.name for tool in (await session.list_tools()).tools}
            assert {"calculate_dti", "calculate_ltv", "evaluate_credit_risk"} <= tools
            for tool, arguments, value in (
                ("calculate_dti", {"monthly_income": 8500, "monthly_debts": 2400}, 28.2),
                ("calculate_ltv", {"loan_amount": 320000, "property_value": 400000}, 80.0),
                ("evaluate_credit_risk", {"credit_score": 742}, 742),
            ):
                result = await session.call_tool(tool, arguments)
                assert not result.isError, result
                data = json.loads(result.content[0].text)
                assert data["value"] == value, data
            print(f"PASS: real HTTP MCP discovery ({len(tools)} tools), DTI 28.2%, LTV 80%, credit 742")


asyncio.run(main())
