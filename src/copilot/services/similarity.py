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
"""Similarity scoring for UX hardening (P2-25).

Calculates weighted similarity scores between candidate table FQNs
and a corpus of prior approved entities.
"""

from __future__ import annotations

import difflib

from copilot.observability import get_logger

log = get_logger(__name__)


def compute_similarity(candidate_fqn: str, approved_fqns: list[str]) -> float:
    """Calculate the maximum similarity score against a list of approved FQNs.

    Uses `difflib.SequenceMatcher` for a basic weighted heuristic. Returns
    a score between 0.0 and 1.0.

    Args:
        candidate_fqn: The FQN of the table being evaluated.
        approved_fqns: A list of previously approved FQNs.

    Returns:
        float: The highest similarity score found, or 0.0 if the approved list is empty.
    """
    if not approved_fqns or not candidate_fqn:
        return 0.0

    max_score = 0.0
    for approved in approved_fqns:
        # A simple string overlap ratio
        score = difflib.SequenceMatcher(None, candidate_fqn, approved).ratio()
        if score > max_score:
            max_score = score

    log.debug("similarity.compute_similarity.result", candidate=candidate_fqn, score=max_score)
    return max_score
