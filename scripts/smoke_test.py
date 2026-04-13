#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai",
# ]
# ///

from __future__ import annotations

import asyncio
import os
import sys

from openai import AsyncOpenAI

SERVER_URL = os.environ.get("SERVER_URL", "http://chatsune-server:8000/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", os.environ.get("VLLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507-FP8"))


async def run() -> None:
    print(f"Connecting to vLLM at {SERVER_URL}...")
    client = AsyncOpenAI(base_url=SERVER_URL, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "Reply with exactly: Connection successful."},
            ],
            max_tokens=20,
            temperature=0.0,
        )
    except Exception as exc:  # broad on purpose for smoke diagnostics
        print(f"FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    text = (response.choices[0].message.content or "").strip()
    print(f"SUCCESS: {text}")


if __name__ == "__main__":
    asyncio.run(run())
