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
"""Pydantic v2 models - single source of truth for shapes."""

from __future__ import annotations

from copilot.models.chat import (
    ChatSession,
    ClassificationJob,
    ErrorEnvelope,
    LineageImpactReport,
    LineageNode,
    PendingSession,
    RiskLevel,
    TagSuggestion,
    ToolCallProposal,
    ToolCallRecord,
    ToolName,
)
from copilot.models.mcp_tools import (
    CreateGlossaryParams,
    CreateGlossaryResponse,
    CreateGlossaryTermParams,
    CreateGlossaryTermResponse,
    GetEntityDetailsParams,
    GetEntityDetailsResponse,
    GetEntityLineageParams,
    GetEntityLineageResponse,
    PatchEntityParams,
    PatchEntityResponse,
    SearchMetadataParams,
    SearchMetadataResponse,
)

__all__ = [
    # chat.py
    "ChatSession",
    "ClassificationJob",
    # mcp_tools.py — Params
    "CreateGlossaryParams",
    # mcp_tools.py — Responses
    "CreateGlossaryResponse",
    "CreateGlossaryTermParams",
    "CreateGlossaryTermResponse",
    "ErrorEnvelope",
    "GetEntityDetailsParams",
    "GetEntityDetailsResponse",
    "GetEntityLineageParams",
    "GetEntityLineageResponse",
    "LineageImpactReport",
    "LineageNode",
    "PatchEntityParams",
    "PatchEntityResponse",
    "PendingSession",
    "RiskLevel",
    "SearchMetadataParams",
    "SearchMetadataResponse",
    "TagSuggestion",
    "ToolCallProposal",
    "ToolCallRecord",
    "ToolName",
]
