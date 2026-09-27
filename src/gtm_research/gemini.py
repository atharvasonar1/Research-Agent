"""Gemini GenerateContent REST adapter for the existing bounded harness."""

import json
import re

import httpx2

from .model import Action, INSTRUCTIONS, ModelError, RetryableModelError
from .schema import TOOLS

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"


def gemini_schema(schema):
    """Translate to Gemini's OpenAPI subset; full validation stays in the harness."""
    result = {key: schema[key] for key in ("type", "description", "enum", "required") if key in schema}
    if "type" in result:
        result["type"] = result["type"].upper()
    if "properties" in schema:
        result["properties"] = {key: gemini_schema(value) for key, value in schema["properties"].items()}
    if "items" in schema:
        result["items"] = gemini_schema(schema["items"])
    return result


class GeminiModel:
    provider = "gemini"

    def __init__(self, model, api_key, client=None):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", model):
            raise ValueError("Use a bare Gemini model ID, not a URL or models/ path")
        self.model = model
        self._api_key = api_key
        self.client = client if client is not None else httpx2.Client(
            trust_env=False, follow_redirects=False,
            transport=httpx2.HTTPTransport(retries=0, trust_env=False),
        )

    def _request(self, method, suffix, timeout, payload=None):
        try:
            response = self.client.request(
                method, f"{API_ROOT}/models/{self.model}{suffix}",
                headers={"x-goog-api-key": self._api_key}, json=payload, timeout=timeout,
            )
            code = response.status_code
            if code in (401, 403):
                raise ModelError("model_auth_error")
            if code == 503:
                raise RetryableModelError("gemini_http_503")
            if code == 429:
                raise ModelError("model_rate_limit")
            if code == 404:
                raise ModelError("model_unavailable")
            if code == 400:
                raise ModelError("model_bad_request")
            if code != 200:
                raise ModelError("model_request_failed")
            value = response.json()
            if not isinstance(value, dict):
                raise ModelError("model_invalid_response")
            return value
        except ModelError:
            raise
        except httpx2.TimeoutException:
            raise ModelError("model_timeout") from None
        except Exception:
            # Never expose response/error content or request headers containing keys.
            raise ModelError("model_request_failed") from None

    def check_availability(self, timeout=10):
        """Metadata check only: this does not establish quota or billing tier."""
        value = self._request("GET", "", timeout)
        if value.get("name") != f"models/{self.model}" or "generateContent" not in value.get("supportedGenerationMethods", []):
            raise ModelError("model_unavailable")
        return {"model": self.model, "generate_content_supported": True,
                "quota_verified": False, "billing_tier_verified": False}

    def decide(self, state, timeout):
        payload = {
            "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(state, ensure_ascii=False)}]}],
            "tools": [{"functionDeclarations": [
                {"name": tool["name"], "description": tool["description"],
                 "parameters": gemini_schema(tool["parameters"])} for tool in TOOLS
            ]}],
            "toolConfig": {"functionCallingConfig": {
                "mode": "ANY", "allowedFunctionNames": [tool["name"] for tool in TOOLS],
            }},
            "generationConfig": {"candidateCount": 1, "maxOutputTokens": 8192},
        }
        value = self._request("POST", ":generateContent", timeout, payload)
        try:
            if value.get("promptFeedback", {}).get("blockReason"):
                raise ModelError("model_blocked_response")
            candidates = value.get("candidates", [])
            if len(candidates) != 1 or candidates[0].get("finishReason") != "STOP":
                raise ModelError("model_incomplete_response")
            calls = [part["functionCall"] for part in candidates[0].get("content", {}).get("parts", [])
                     if "functionCall" in part]
            if len(calls) != 1:
                raise ModelError("model_expected_one_tool_call")
            call = calls[0]
            if call.get("name") not in {tool["name"] for tool in TOOLS} or not isinstance(call.get("args"), dict):
                raise ModelError("model_invalid_arguments")
            raw_usage = value.get("usageMetadata", {})
            usage = {target: raw_usage.get(source) for target, source in (
                ("input_tokens", "promptTokenCount"), ("output_tokens", "candidatesTokenCount"),
                ("thinking_tokens", "thoughtsTokenCount"), ("total_tokens", "totalTokenCount"),
            )}
            return Action(call["name"], call["args"], usage)
        except ModelError:
            raise
        except (KeyError, TypeError, AttributeError):
            raise ModelError("model_invalid_response") from None

    def close(self):
        self.client.close()
