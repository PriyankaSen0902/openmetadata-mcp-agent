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
"""Module G Layer-1 input neutralization for LLM prompts.

Per .idea/Plan/Security/PromptInjectionMitigation.md: catalog content
fetched from OpenMetadata is attacker-controlled (any catalog editor can plant
a prompt-injection payload in a column description). This module is the FIRST
of five defense layers. It MUST be called on every catalog field before that
field appears in an LLM prompt.

Real-world precedent: hackathon PR #27506 shipped notebook code that
interpolated raw OM API response data into LLM prompts. Gitar-bot's automated
review flagged it as indirect prompt injection. We will not repeat that.
"""

from __future__ import annotations

import re

# Patterns that strongly suggest the user is trying to override prior
# instructions. Tagged (not removed) so the LLM can still see the content
# but treats it skeptically; the [SUSPICIOUS:] prefix also surfaces in the UI.
INSTRUCTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?i)ignore\s+(?:all\s+|the\s+)?(?:previous|prior|above|earlier)\s+(?:instructions?|prompts?|rules?)"
    ),
    re.compile(r"(?i)disregard\s+(?:all\s+|the\s+)?(?:previous|prior|above|earlier)"),
    re.compile(r"(?i)forget\s+(?:all\s+|the\s+)?(?:previous|prior|above|earlier)"),
    re.compile(r"(?i)you\s+are\s+now\s+(?:a\s+)?(?:different|new)"),
    re.compile(r"(?i)system\s*[:>]\s*"),
    re.compile(r"(?i)assistant\s*[:>]\s*"),
    re.compile(r"\[INST\]"),
    re.compile(r"(?i)\bjailbreak\b"),
]

# Zero-width characters used to hide instruction injection.
ZERO_WIDTH = re.compile(r"[\u200B-\u200D\uFEFF]")

DEFAULT_MAX_LEN = 500
TRUNCATION_SUFFIX = " ...[truncated]"


def neutralize(field_value: str | None, max_len: int = DEFAULT_MAX_LEN) -> str:
    """Make a string safe to embed in an LLM prompt.

    Behavior:
        - Returns "" if input is None or empty.
        - Strips zero-width Unicode (anti-obfuscation).
        - Tags any instruction-injection pattern with [SUSPICIOUS:] prefix
          (content is preserved for transparency in the audit log; the LLM
          is signaled to treat it skeptically; the UI can highlight it).
        - HTML-escapes < > & " ' so the LLM's downstream rendering cannot
          embed clickable HTML or break out of a markdown context.
        - Truncates to max_len chars with " ...[truncated]" suffix.

    This is Layer 1 of the five-layer Module G defense. Subsequent layers:
        2. Structured-message prompt assembly (system role vs user role)
        3. Pydantic output validation (ToolCallProposal.model_validate)
        4. Tool allowlist enforcement (services/agent.py)
        5. HITL confirmation gate (POST /api/v1/chat/confirm)

    Args:
        field_value: the raw catalog string from OpenMetadata.
        max_len: maximum output length. Default 500 chars per NFRs.md.

    Returns:
        Safe string suitable for prompt assembly.
    """
    if not field_value:
        return ""

    text = ZERO_WIDTH.sub("", field_value)

    for pattern in INSTRUCTION_PATTERNS:
        text = pattern.sub(lambda m: f"[SUSPICIOUS:{m.group(0)}]", text)

    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

    if len(text) > max_len:
        text = text[: max_len - len(TRUNCATION_SUFFIX)] + TRUNCATION_SUFFIX

    return text


def is_suspicious(neutralized_text: str) -> bool:
    """Return True if the neutralized text contains a [SUSPICIOUS:] marker.

    Useful for the UI to flag rows in the auto-classification confirmation modal
    that came from columns with planted injection patterns.
    """
    return "[SUSPICIOUS:" in neutralized_text
