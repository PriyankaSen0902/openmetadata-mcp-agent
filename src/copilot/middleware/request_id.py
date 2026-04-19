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
"""Generate a UUID per HTTP request, bind it to structlog contextvars.

Per .idea/Plan/Project/NFRs.md NFR-06: every log line + every error envelope
+ every metrics label must carry the same request_id end-to-end.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-Id"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Bind a fresh UUID per request to structlog contextvars and response header.

    Honors an inbound X-Request-Id header if present and parseable as UUID;
    otherwise generates a new UUID v4.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = self._extract_or_generate(request)
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=str(request_id))

        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

        response.headers[REQUEST_ID_HEADER] = str(request_id)
        return response

    @staticmethod
    def _extract_or_generate(request: Request) -> UUID:
        inbound = request.headers.get(REQUEST_ID_HEADER)
        if inbound:
            try:
                return UUID(inbound)
            except (ValueError, TypeError):
                pass
        return uuid4()
