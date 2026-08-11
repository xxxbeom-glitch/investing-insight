from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.settings import Settings


class ModelUnavailableError(RuntimeError):
    """Requested model cannot be used — fail closed, never silent fallback."""


def resolve_requested_model(model: str) -> str:
    """Shared resolution gate used by the live client and eval harness. No silent remap."""
    name = (model or "").strip()
    if not name:
        raise ModelUnavailableError("empty model")
    upper = name.upper().replace("-", "_")
    if "DOES_NOT_EXIST" in upper or upper.startswith("THIS_") or "NOT_AVAILABLE" in upper:
        raise ModelUnavailableError(f"unavailable model: {model}")
    return name


class ResponsesApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResponsesResult:
    response_id: str | None
    resolved_model: str
    output_text: str
    raw: dict[str, Any]
    token_usage: dict[str, Any] | None


def _extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"]:
        return payload["output_text"]
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    if chunks:
        return "".join(chunks)
    raise ResponsesApiError("Responses API returned no output text")


def _sanitize_openai_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """OpenAI strict json_schema rejects $id/$schema; keep nested objects strict."""
    drop = {"$schema", "$id"}
    out: dict[str, Any] = {}
    for k, v in schema.items():
        if k in drop:
            continue
        if isinstance(v, dict):
            out[k] = _sanitize_openai_schema(v)
        elif isinstance(v, list):
            out[k] = [_sanitize_openai_schema(i) if isinstance(i, dict) else i for i in v]
        else:
            out[k] = v
    return out


class OpenAIResponsesClient:
    def __init__(self, settings: Settings, *, timeout: float = 120.0):
        if not settings.openai_api_key:
            raise ResponsesApiError("OPENAI_API_KEY missing")
        self._key = settings.openai_api_key
        self._timeout = timeout

    def create_structured(
        self,
        *,
        model: str,
        reasoning_effort: str,
        system_prompt: str,
        user_payload: dict[str, Any],
        output_schema: dict[str, Any],
        schema_name: str,
    ) -> ResponsesResult:
        model = resolve_requested_model(model)
        clean_schema = _sanitize_openai_schema(output_schema)
        body = {
            "model": model,
            "reasoning": {"effort": reasoning_effort},
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
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
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
            # only treat as model unavailable when message suggests model issue
            lowered = (msg or "").lower()
            if "model" in lowered or resp.status_code == 404:
                raise ModelUnavailableError(f"{code}: {msg}")
        if resp.status_code >= 400:
            raise ResponsesApiError(f"responses http {resp.status_code}: {resp.text[:500]}")
        text = _extract_output_text(data)
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else None
        resolved = str(data.get("model") or model)
        if resolved != model:
            # profile mismatch / silent remap is forbidden
            raise ModelUnavailableError(
                f"resolved model {resolved!r} != requested {model!r} (no silent fallback)"
            )
        return ResponsesResult(
            response_id=str(data.get("id")) if data.get("id") else None,
            resolved_model=resolved,
            output_text=text,
            raw=data,
            token_usage=usage,
        )
