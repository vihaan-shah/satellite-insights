"""
IBM watsonx.ai client — uses the ibm-watsonx-ai SDK (no raw HTTP).
Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file.

Docs: https://ibm.github.io/watson-machine-learning-sdk/
"""
import os
import warnings
from typing import Optional

# Suppress the deprecation + disclaimer warnings from the SDK in normal use
warnings.filterwarnings("ignore", category=Warning, module="ibm_watsonx_ai")


def _creds():
    from ibm_watsonx_ai import Credentials
    return Credentials(
        url=os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
        api_key=os.getenv("WATSONX_API_KEY", ""),
    )


def _model_id() -> str:
    # Default to llama-3-3-70b-instruct — confirmed available in us-south.
    # Override via GRANITE_MODEL in .env if your region has different models.
    return os.getenv("GRANITE_MODEL", "meta-llama/llama-3-3-70b-instruct")


def generate_text(
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.4,
    stop_sequences: Optional[list[str]] = None,
) -> str:
    """
    Generate text via the watsonx.ai SDK.

    Falls back to a helpful message when no API key is configured.
    """
    api_key = os.getenv("WATSONX_API_KEY", "")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")

    if not api_key:
        return (
            "IBM Granite API key not configured. Add WATSONX_API_KEY to your "
            ".env file and restart the backend to enable AI-generated briefs."
        )

    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params

        model = ModelInference(
            model_id=_model_id(),
            credentials=_creds(),
            project_id=project_id,
            params={
                Params.MAX_NEW_TOKENS: max_new_tokens,
                Params.TEMPERATURE: temperature,
                Params.STOP_SEQUENCES: stop_sequences or [],
            },
        )

        result = model.generate_text(prompt)
        return result.strip() if result else "No response generated."

    except Exception as exc:
        return f"[watsonx.ai error] {exc}"
