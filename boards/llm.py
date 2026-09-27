"""Thin xAI client. Chat Completions for structured scoring; Responses API with server-side
web_search / x_search tools for live research. A MockLLM stands in for dry runs with no key."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

XAI_BASE_URL = "https://api.x.ai/v1"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    calls: int = 0
    by_model: dict = field(default_factory=dict)

    def add(self, model: str, inp: int, out: int, tools: int = 0) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.tool_calls += tools
        self.calls += 1
        m = self.by_model.setdefault(model, [0, 0])
        m[0] += inp
        m[1] += out

    def cost(self, prices: dict) -> float:
        """prices: {model: [usd_per_1M_in, usd_per_1M_out], "tool_call": usd_per_call}"""
        total = sum(inp / 1e6 * prices.get(m, [0, 0])[0] + out / 1e6 * prices.get(m, [0, 0])[1]
                    for m, (inp, out) in self.by_model.items())
        return round(total + self.tool_calls * prices.get("tool_call", 0.005), 4)


def extract_json(text: str):
    """Parse the first JSON object or array in a model reply (tolerates code fences)."""
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON in reply: {text[:200]!r}")


class XaiLLM:
    def __init__(self, api_key: str | None = None):
        from openai import OpenAI

        key = api_key or os.environ.get("XAI_API_KEY")
        if not key:
            raise RuntimeError("XAI_API_KEY is not set (use --mock for a dry run without it)")
        self.client = OpenAI(api_key=key, base_url=XAI_BASE_URL, timeout=180)
        self.usage = Usage()

    def json(self, model: str, system: str, user: str, schema: dict, name: str = "result") -> dict:
        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={"type": "json_schema",
                             "json_schema": {"name": name, "schema": schema, "strict": True}},
            temperature=0.2,
        )
        u = resp.usage
        self.usage.add(model, getattr(u, "prompt_tokens", 0), getattr(u, "completion_tokens", 0))
        return extract_json(resp.choices[0].message.content)

    def research(self, model: str, prompt: str, tools: tuple[str, ...] = ("x_search", "web_search")):
        resp = self.client.responses.create(
            model=model,
            input=[{"role": "user", "content": prompt}],
            tools=[{"type": t} for t in tools],
        )
        u = getattr(resp, "usage", None)
        tool_calls = sum(1 for item in getattr(resp, "output", []) or []
                         if str(getattr(item, "type", "")).endswith("_call"))
        self.usage.add(model, getattr(u, "input_tokens", 0) or 0,
                       getattr(u, "output_tokens", 0) or 0, tool_calls)
        return extract_json(resp.output_text)


class MockLLM:
    """Deterministic stand-in with no API key: fits fall back to the heuristic score, and
    drafts and contacts are clearly marked [mock]."""

    def __init__(self):
        self.usage = Usage()

    def json(self, model: str, system: str, user: str, schema: dict, name: str = "result") -> dict:
        self.usage.add(model, len(system + user) // 4, 120)
        if name == "fit":
            return {"fit": -1, "why": "[mock] Fit reasoning appears here on a real run.",
                    "angle": "EvalCI", "flags": [], "confirmed_lane": "keep"}
        if name == "draft":
            return {"draft": "[mock] A <110-word message with one specific hook appears here.",
                    "resume_edits": ["[mock] Resume bullet swap 1", "[mock] Resume bullet swap 2"]}
        return {}

    def research(self, model: str, prompt: str, tools=("x_search", "web_search")):
        self.usage.add(model, len(prompt) // 4, 150, len(tools))
        return {"contacts": [{"name": "[mock] Engineer on the team", "handle": "@example",
                              "role": "Member of Technical Staff",
                              "hook": "[mock] A recent post of theirs to mention",
                              "hook_url": "https://x.com/example/status/0"}]}
