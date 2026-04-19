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
"""OpenAI client - circuit-breaker-wrapped chat-completions caller.

Per .idea/Plan/Project/NFRs.md:
  - timeout: 8.0s (settings.openai_timeout_seconds)
  - retry: 2 attempts (uses openai SDK's built-in max_retries)
  - circuit breaker: open after 5 consecutive failures, 60s cooldown
  - token budget per session enforced upstream in services/agent.py

P2-04 task: implement chat-completion with structured output for ToolCallProposal.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import pybreaker
from openai import AsyncOpenAI

from copilot.config import get_settings
from copilot.middleware.error_envelope import LlmUnavailable  # LlmInvalidOutput used in P2-04 impl
from copilot.observability import get_logger

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


# TODO P2-04: implement chat completion with structured output.
# Pseudocode:
#
#   @openai_breaker
#   async def call_chat(
#       messages: list[dict[str, str]],
#       *,
#       max_tokens: int = 1000,
#   ) -> dict[str, Any]:
#       client = _get_client()
#       try:
#           response = await client.chat.completions.create(
#               model=get_settings().openai_model,
#               messages=messages,
#               max_tokens=max_tokens,
#           )
#       except APITimeoutError as exc:
#           raise LlmUnavailable("openai timeout") from exc
#       except APIConnectionError as exc:
#           raise LlmUnavailable("openai connection") from exc
#       except RateLimitError as exc:
#           raise LlmUnavailable("openai rate limit") from exc
#       choice = response.choices[0].message
#       if not choice.content:
#           raise LlmInvalidOutput("empty response")
#       return {
#           "content": choice.content,
#           "tokens_prompt": response.usage.prompt_tokens if response.usage else 0,
#           "tokens_completion": response.usage.completion_tokens if response.usage else 0,
#       }


async def call_chat(messages: list[dict[str, str]], *, max_tokens: int = 1000) -> dict[str, Any]:
    """Stubbed chat-completion. Implement in P2-04."""
    log.warning(
        "openai.call_chat.not_implemented", message_count=len(messages), max_tokens=max_tokens
    )
    raise LlmUnavailable("openai_client.call_chat not implemented yet (P2-04)")
