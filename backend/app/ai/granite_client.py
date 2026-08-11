"""
IBM Granite client — wraps the IBM watsonx.ai Inference API.
Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file.

Docs: https://cloud.ibm.com/apidocs/watsonx-ai
"""
import os
import httpx
from typing import Optional

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL = os.getenv("GRANITE_MODEL", "ibm/granite-13b-instruct-v2")

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

_cached_token: Optional[str] = None


def _get_iam_token() -> str:
    """Exchange IBM API key for a short-lived IAM bearer token."""
    global _cached_token
    if _cached_token:
        return _cached_token

    resp = httpx.post(
        IAM_TOKEN_URL,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": WATSONX_API_KEY,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    _cached_token = resp.json()["access_token"]
    return _cached_token


def generate_text(
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.3,
    stop_sequences: Optional[list[str]] = None,
) -> str:
    """
    Call the watsonx.ai text generation endpoint with IBM Granite.

    Falls back to a placeholder string when no API key is configured
    (useful for local development without credentials).
    """
    if not WATSONX_API_KEY:
        return (
            "[Granite offline — set WATSONX_API_KEY] "
            "This would be a live AI-generated situation brief."
        )

    token = _get_iam_token()
    url = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"

    payload = {
        "model_id": GRANITE_MODEL,
        "project_id": WATSONX_PROJECT_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "sample",
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "stop_sequences": stop_sequences or ["\n\n"],
        },
    }

    resp = httpx.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()

    results = resp.json().get("results", [])
    if results:
        return results[0].get("generated_text", "").strip()
    return "No response generated."
