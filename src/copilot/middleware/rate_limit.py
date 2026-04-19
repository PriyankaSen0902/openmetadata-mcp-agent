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
"""Rate-limit middleware via slowapi. Limits per .idea/Plan/Project/NFRs.md."""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.responses import Response


def build_limiter() -> Limiter:
    """Build the per-IP limiter. Routes apply specific limits via @limiter.limit(...)."""
    return Limiter(
        key_func=get_remote_address,
        default_limits=["60/minute"],  # generous default; routes may tighten
    )


def attach_limiter(app: FastAPI, limiter: Limiter) -> None:
    """Attach the limiter to the FastAPI app."""
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    # slowapi's handler signature is narrower than FastAPI's exception_handler
    # type stub expects; cast to the broader Starlette signature.
    handler = cast(
        "type[Response]",
        _rate_limit_exceeded_handler,
    )
    app.add_exception_handler(RateLimitExceeded, handler)
