#  Copyright 2026 Collate Inc.
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""OpenAI client — circuit-breaker-wrapped chat-completions caller.

Per .idea/Plan/Project/NFRs.md:
  - timeout: 8.0 s (settings.openai_timeout_seconds)
  - retry: 2 attempts (uses openai SDK's built-in max_retries)
  - circuit breaker: open after 5 consecutive failures, 60 s cooldown
  - token budget per session enforced upstream in services/agent.py

Implements P1-03 companion: call_chat + call_chat_json for the agent.
"""

from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Any

import pybreaker
from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from copilot.config import get_settings
from copilot.middleware.error_envelope import LlmInvalidOutput, LlmUnavailable
from copilot.observability import get_logger
from copilot.observability.metrics import (
    agent_llm_calls_total,
    agent_llm_tokens_used_total,
)

log = get_logger(__name__)

openai_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="openai",
)


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    """Build the OpenAI client lazily so tests can override settings first."""
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )


@openai_breaker
async def call_chat(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1000,
) -> dict[str, Any]:
    """Send a chat-completion request to OpenAI with circuit-breaker protection.

    Args:
        messages: Chat messages in OpenAI format ([{"role": ..., "content": ...}]).
        max_tokens: Maximum tokens in the completion response.

    Returns:
        Dict with keys: ``content`` (str), ``tokens_prompt`` (int),
        ``tokens_completion`` (int).

    Raises:
        LlmUnavailable: On timeout, connection, rate-limit, or circuit-open errors.
        LlmInvalidOutput: When the model returns an empty response.
    """
    settings = get_settings()
    model = settings.openai_model
    log.info("openai.call_chat.start", model=model, message_count=len(messages))
    start = time.monotonic()

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
        )
    except APITimeoutError as exc:
        _record_failure(model, start)
        raise LlmUnavailable("OpenAI request timed out") from exc
    except APIConnectionError as exc:
        _record_failure(model, start)
        raise LlmUnavailable("OpenAI connection failed") from exc
    except RateLimitError as exc:
        _record_failure(model, start)
        raise LlmUnavailable("OpenAI rate limit exceeded") from exc
    except pybreaker.CircuitBreakerError as exc:
        _record_failure(model, start)
        raise LlmUnavailable("OpenAI circuit breaker is open — too many recent failures") from exc
    except Exception as exc:
        _record_failure(model, start)
        raise LlmUnavailable(f"OpenAI unexpected error: {type(exc).__name__}") from exc

    choice = response.choices[0].message if response.choices else None
    if not choice or not choice.content:
        _record_failure(model, start)
        raise LlmInvalidOutput("OpenAI returned an empty response")

    tokens_prompt = response.usage.prompt_tokens if response.usage else 0
    tokens_completion = response.usage.completion_tokens if response.usage else 0

    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.info(
        "openai.call_chat.complete",
        model=model,
        elapsed_ms=elapsed_ms,
        tokens_prompt=tokens_prompt,
        tokens_completion=tokens_completion,
    )

    # Record metrics
    agent_llm_calls_total.labels(model=model, outcome="ok").inc()
    agent_llm_tokens_used_total.labels(direction="prompt", model=model).inc(tokens_prompt)
    agent_llm_tokens_used_total.labels(direction="completion", model=model).inc(tokens_completion)

    return {
        "content": choice.content,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
    }


async def call_chat_json(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1000,
) -> dict[str, Any]:
    """Call chat completion and parse the response as JSON.

    Args:
        messages: Chat messages in OpenAI format.
        max_tokens: Maximum tokens in the completion response.

    Returns:
        Parsed JSON dict from the model's response.

    Raises:
        LlmUnavailable: On API errors.
        LlmInvalidOutput: When the model's response is not valid JSON.
    """
    result = await call_chat(messages, max_tokens=max_tokens)
    content = result["content"]

    # Strip markdown code fences if present
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    try:
        parsed: dict[str, Any] = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("openai.json_parse_failed", content_preview=text[:200])
        raise LlmInvalidOutput(f"Model response is not valid JSON: {exc}") from exc

    return parsed


def _record_failure(model: str, start: float) -> None:
    """Record a failed LLM call in metrics and logs."""
    elapsed_ms = int((time.monotonic() - start) * 1000)
    log.warning("openai.call_chat.failed", model=model, elapsed_ms=elapsed_ms)
    agent_llm_calls_total.labels(model=model, outcome="fail").inc()
