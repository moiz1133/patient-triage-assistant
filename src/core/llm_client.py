import time

import tiktoken
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError
from pydantic import BaseModel

from src.config import config
from src.core.logger import logger

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=config.openai_api_key)
    return _client


class LLMExtractionError(Exception):
    pass


def call_structured(
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
    temperature: float | None = None,
    max_retries: int = 2,
) -> BaseModel:
    if temperature is None:
        temperature = config.openai_temperature

    client = _get_client()
    retryable = (RateLimitError, APIConnectionError, APITimeoutError)
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            t0 = time.monotonic()
            response = client.beta.chat.completions.parse(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_model,
                temperature=temperature,
                max_tokens=config.openai_max_tokens,
            )
            latency_ms = round((time.monotonic() - t0) * 1000)
            usage = response.usage
            logger.info(
                "LLM call success | model={} prompt_tokens={} completion_tokens={} latency_ms={}",
                config.openai_model,
                usage.prompt_tokens if usage else "?",
                usage.completion_tokens if usage else "?",
                latency_ms,
            )
            return response.choices[0].message.parsed

        except retryable as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "LLM transient error (attempt {}/{}) — retrying in {}s | {}",
                    attempt + 1,
                    max_retries + 1,
                    wait,
                    exc,
                )
                time.sleep(wait)
            else:
                logger.error(
                    "LLM call failed after {} attempts | {}", max_retries + 1, exc
                )
                raise LLMExtractionError(
                    f"LLM call failed after {max_retries + 1} attempts: {exc}"
                ) from exc

    # unreachable, but satisfies type checkers
    raise LLMExtractionError(f"LLM call failed: {last_exc}")


def estimate_tokens(text: str) -> int:
    """Count tokens in text using tiktoken for the configured model."""
    try:
        enc = tiktoken.encoding_for_model(config.openai_model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
