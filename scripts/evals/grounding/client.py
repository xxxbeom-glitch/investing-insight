"""Thin eval LLM client. create_json(system, user) -> dict. OpenAI only for MVP."""

from __future__ import annotations

import json
import os
from typing import Any, Protocol

import httpx

from app.research.openai_responses import (
    ModelUnavailableError,
    ResponsesApiError,
    _extract_output_text,
    _sanitize_openai_schema,
    resolve_requested_model,
)


class EvalClient(Protocol):
    def create_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        *,
        output_schema: dict[str, Any],
        schema_name: str,
        model: str,
        reasoning_effort: str,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        ...


class OpenAIEvalClient:
    """OpenAI Responses JSON. Does not wrap production agent roles."""

    def __init__(self, api_key: str, *, timeout: float = 120.0) -> None:
        key = (api_key or "").strip()
        if not key:
            raise ResponsesApiError("OPENAI_API_KEY missing")
        self._key = key
        self._timeout = timeout
        self.usage_totals = {"input_tokens": 0, "output_tokens": 0, "requests": 0}

    def create_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        *,
        output_schema: dict[str, Any],
        schema_name: str,
        model: str,
        reasoning_effort: str,
        max_output_tokens: int,
    ) -> dict[str, Any]:
        requested = resolve_requested_model(model)
        clean_schema = _sanitize_openai_schema(output_schema)
        body = {
            "model": requested,
            "reasoning": {"effort": reasoning_effort},
            "max_output_tokens": int(max_output_tokens),
            "input": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": clean_schema,
                    "strict": True,
                }
            },
        }
        with httpx.Client(timeout=self._timeout) as http:
            resp = http.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        data = resp.json() if resp.content else {}
        if resp.status_code in {400, 404} or (
            isinstance(data, dict)
            and str((data.get("error") or {}).get("code") or "").lower()
            in {"model_not_found", "invalid_model", "model_not_available"}
        ):
            err = data.get("error") if isinstance(data, dict) else {}
            msg = (err or {}).get("message") or resp.text
            code = (err or {}).get("code") or f"http_{resp.status_code}"
            lowered = (msg or "").lower()
            if "model" in lowered or resp.status_code == 404:
                raise ModelUnavailableError(f"{code}: {msg}")
        if resp.status_code >= 400:
            raise ResponsesApiError(f"responses http {resp.status_code}: {resp.text[:500]}")
        text = _extract_output_text(data)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        resolved = str(data.get("model") or requested)
        if resolved != requested:
            raise ModelUnavailableError(
                f"resolved model {resolved!r} != requested {requested!r} (no silent fallback)"
            )
        self._add_usage(usage)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResponsesApiError(f"eval JSON parse failed: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ResponsesApiError("eval JSON was not an object")
        return parsed

    def _add_usage(self, usage: dict[str, Any]) -> None:
        self.usage_totals["requests"] += 1
        self.usage_totals["input_tokens"] += int(usage.get("input_tokens") or 0)
        self.usage_totals["output_tokens"] += int(usage.get("output_tokens") or 0)


def create_client(provider: str, *, api_key: str | None = None) -> OpenAIEvalClient:
    name = (provider or "openai").strip().lower()
    if name != "openai":
        raise NotImplementedError(f"provider not implemented: {provider}")
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
    return OpenAIEvalClient(key)
