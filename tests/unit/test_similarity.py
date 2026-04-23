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
from copilot.services.similarity import compute_similarity


def test_compute_similarity_empty():
    assert compute_similarity("", ["test_fqn"]) == 0.0
    assert compute_similarity("test_fqn", []) == 0.0
    assert compute_similarity("", []) == 0.0


def test_compute_similarity_exact_match():
    candidate = "db.schema.table"
    approved = ["db.schema.other", "db.schema.table"]
    score = compute_similarity(candidate, approved)
    assert score == 1.0


def test_compute_similarity_partial_match():
    candidate = "db.schema.orders"
    approved = ["db.schema.users", "db.schema.products"]
    score = compute_similarity(candidate, approved)
    # difflib score should be > 0 but < 1
    assert 0.0 < score < 1.0
