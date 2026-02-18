from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(slots=True)
class PlanDraft:
    steps: list[str]
    used_model: str


class LLMClient:
    async def decompose_goal(self, goal: str) -> PlanDraft:
        raise NotImplementedError


class HeuristicLLMClient(LLMClient):
    """Deterministic low-cost fallback used when no model endpoint is configured."""

    async def decompose_goal(self, goal: str) -> PlanDraft:
        cleaned = goal.strip()
        if not cleaned:
            return PlanDraft(["Clarify user intent"], "heuristic")

        candidates = [p.strip(" .") for p in cleaned.replace(";", ".").split(".") if p.strip()]
        if not candidates:
            candidates = [cleaned]
        steps = [f"Understand: {candidates[0]}"]
        steps.extend(f"Subtask: {c}" for c in candidates[1:3])
        if "run " in cleaned.lower():
            command = cleaned.lower().split("run ", 1)[1].strip()
            if command:
                steps.append(f"Execute command: {command}")
        if "email" in cleaned.lower():
            steps.append("Prepare email action safely")
        steps.append("Summarize outcome for user")
        return PlanDraft(steps, "heuristic")


class OllamaLLMClient(LLMClient):
    """Optional local LLM integration via Ollama HTTP API (no extra deps)."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def decompose_goal(self, goal: str) -> PlanDraft:
        prompt = (
            "Decompose the goal into 3-6 concise executable steps. "
            "Return strict JSON object with key 'steps' as array of strings.\n"
            f"Goal: {goal}"
        )
        payload = {"model": self.model, "prompt": prompt, "stream": False, "format": "json"}

        def _request() -> str:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                body = json.loads(response.read().decode("utf-8"))
                return body.get("response", "")

        try:
            response_text = await asyncio.to_thread(_request)
            parsed = json.loads(response_text) if response_text else {}
            steps = [str(s).strip() for s in parsed.get("steps", []) if str(s).strip()]
            if not steps:
                raise ValueError("empty_steps")
            return PlanDraft(steps[:6], f"ollama:{self.model}")
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            fallback = HeuristicLLMClient()
            return await fallback.decompose_goal(goal)


def build_llm_client() -> LLMClient:
    model = os.getenv("OPTICLAW_OLLAMA_MODEL", "qwen2.5:3b")
    base_url = os.getenv("OPTICLAW_OLLAMA_URL")
    if base_url:
        return OllamaLLMClient(base_url=base_url, model=model)
    return HeuristicLLMClient()
