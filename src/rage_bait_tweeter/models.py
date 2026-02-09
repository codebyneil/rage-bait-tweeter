"""Unified LLM client supporting OpenAI, Anthropic, and Google."""

import json
import logging
import re

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """Extract JSON from a model response, handling markdown code fences."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


def _get_provider(model_id: str) -> str:
    """Determine the provider from a model ID."""
    if model_id.startswith(("gpt-", "o1", "o3", "o4", "chatgpt-")):
        return "openai"
    elif model_id.startswith("claude-"):
        return "anthropic"
    elif model_id.startswith("gemini-"):
        return "google"
    else:
        raise ValueError(f"Unknown model provider for: {model_id}")


def complete(model_id: str, prompt: str, *, json_mode: bool = False) -> str:
    """Send a prompt to the specified model and return the response text."""
    provider = _get_provider(model_id)
    logger.debug("Calling %s (provider: %s)", model_id, provider)

    if provider == "openai":
        return _openai_complete(model_id, prompt, json_mode=json_mode)
    elif provider == "anthropic":
        return _anthropic_complete(model_id, prompt, json_mode=json_mode)
    elif provider == "google":
        return _google_complete(model_id, prompt, json_mode=json_mode)
    raise ValueError(f"Unknown provider: {provider}")


def _openai_complete(model_id: str, prompt: str, *, json_mode: bool) -> str:
    import openai

    client = openai.OpenAI()
    kwargs: dict = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return response.choices[0].message.content or ""


def _anthropic_complete(model_id: str, prompt: str, *, json_mode: bool) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model_id,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _google_complete(model_id: str, prompt: str, *, json_mode: bool) -> str:
    from google import genai
    from google.genai.types import GenerateContentConfig

    client = genai.Client()
    config = None
    if json_mode:
        config = GenerateContentConfig(response_mime_type="application/json")
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=config,
    )
    return response.text or ""
