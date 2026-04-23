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
"""Generate a Bot JWT from a running OpenMetadata instance.

Connects to the OM REST API, authenticates as admin, looks up the
ingestion-bot, and generates a JWT with configurable expiry.  The token
is printed to stdout so the user can paste it into .env as AI_SDK_TOKEN.

The script uses only the Python standard library via ``urllib``.

Usage:
    python scripts/generate_bot_jwt.py
    python scripts/generate_bot_jwt.py --host http://remote:8585
    python scripts/generate_bot_jwt.py --expiry-days 60
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OM_URL = "http://localhost:8585"
API_PREFIX = "/api/v1"
BOT_NAME = "ingestion-bot"
REQUEST_TIMEOUT = 10
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_EMAIL = "admin@open-metadata.org"

EXPIRY_MAP: dict[int, str] = {
    7: "7",
    30: "30",
    60: "60",
    90: "90",
    0: "Unlimited",
}


def _api_request(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """Make an HTTP request to the OM REST API."""
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(  # noqa: S310 - OM URL is local or explicitly user-supplied
        url,
        data=body,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        print(
            f"FAIL: {method} {url} -> HTTP {exc.code}: {response_body[:300]}",
            file=sys.stderr,
        )
        return None
    except (urllib.error.URLError, TimeoutError, http.client.HTTPException) as exc:
        print(f"FAIL: {method} {url} -> {exc}", file=sys.stderr)
        return None


def _resolve_expiry(days: int) -> str:
    """Map user-requested expiry days to the OM JWTTokenExpiry enum value."""
    if days in EXPIRY_MAP:
        return EXPIRY_MAP[days]
    if days < 0:
        days = 0
    closest = min(EXPIRY_MAP.keys(), key=lambda k: abs(k - days) if k > 0 else 9999)
    print(
        f"  (OM supports expiry of {sorted(k for k in EXPIRY_MAP if k > 0)} days "
        f"or Unlimited; rounding {days} -> {closest})"
    )
    return EXPIRY_MAP[closest]


def check_health(base_url: str) -> bool:
    """Verify the OM server is reachable.

    OpenMetadata 1.6.x does not expose ``GET /api/v1/health`` on the default image;
    we use ``GET /api/v1/system/version`` (same signal as ``scripts/smoke_test.py``).
    """
    url = f"{base_url}{API_PREFIX}/system/version"
    result = _api_request(url)
    if result is None:
        return False
    version = result.get("version")
    if not isinstance(version, str) or not version:
        print(f"FAIL: version check returned unexpected payload: {result}", file=sys.stderr)
        return False
    print("  OM server reachable (version check)")
    return True


def _login_candidates(username: str) -> list[str]:
    """Return the login identifiers to try for the provided username."""
    if username == DEFAULT_ADMIN_USERNAME:
        return [DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL]
    return [username]


def _password_for_login_api(password: str) -> str:
    """OM 1.6.x ``/users/login`` expects the password as Base64 (ASCII string)."""
    return base64.b64encode(password.encode("utf-8")).decode("ascii")


def _extract_access_token(result: dict[str, Any]) -> str | None:
    """Extract an access token from an OM login response."""
    token = result.get("accessToken")
    if isinstance(token, str) and token:
        return token

    token_data = result.get("data", {})
    if isinstance(token_data, dict):
        nested_token = token_data.get("accessToken")
        if isinstance(nested_token, str) and nested_token:
            return nested_token

    return None


def login_admin(base_url: str, username: str, password: str) -> str | None:
    """Authenticate as admin and return a session JWT."""
    url = f"{base_url}{API_PREFIX}/users/login"
    headers = {"Content-Type": "application/json"}

    final_result: dict[str, Any] | None = None
    for candidate in _login_candidates(username):
        payload = {"email": candidate, "password": _password_for_login_api(password)}
        result = _api_request(url, method="POST", data=payload, headers=headers)
        if result is None:
            continue

        final_result = result
        token = _extract_access_token(result)
        if token:
            if candidate != username:
                print(f"  Login required email-form username; retried as {candidate}.")
            return token

    if final_result is not None:
        print(f"FAIL: login response missing accessToken: {final_result}", file=sys.stderr)
    return None


def get_bot_user(base_url: str, auth_token: str) -> dict[str, Any] | None:
    """Look up the ingestion-bot and return its associated user entity."""
    bot_url = f"{base_url}{API_PREFIX}/bots/name/{BOT_NAME}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }
    bot = _api_request(bot_url, headers=headers)
    if bot is None:
        print(
            f"FAIL: bot '{BOT_NAME}' not found — is OM fully initialised?",
            file=sys.stderr,
        )
        return None

    bot_user_ref = bot.get("botUser", {})
    user_id = bot_user_ref.get("id")
    user_name = bot_user_ref.get("name") or bot_user_ref.get("fullyQualifiedName")
    if not user_id:
        print(f"FAIL: bot '{BOT_NAME}' has no associated user", file=sys.stderr)
        return None

    user_url = f"{base_url}{API_PREFIX}/users/{user_id}"
    user_data = _api_request(
        user_url,
        headers=headers,
    )
    if user_data is None:
        print(f"FAIL: could not fetch user {user_name} (id={user_id})", file=sys.stderr)
        return None

    print(f"  Found bot user: {user_data.get('name', user_name)}")
    return user_data


def generate_token(
    base_url: str,
    auth_token: str,
    user_data: dict[str, Any],
    expiry_value: str,
) -> str | None:
    """Generate a new JWT using ``PUT /api/v1/users/generateToken/{id}`` (OM 1.6.x).

    Bot-linked users cannot be updated via ``PUT /api/v1/users`` with a full entity body;
    the server returns 400 if the bot user is already bound to a bot.
    """
    user_id = user_data["id"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }
    url = f"{base_url}{API_PREFIX}/users/generateToken/{user_id}"
    body = {"JWTTokenExpiry": expiry_value}
    result = _api_request(url, method="PUT", data=body, headers=headers)
    if result is None:
        print("FAIL: could not generate bot JWT", file=sys.stderr)
        return None

    jwt_token = result.get("JWTToken") or result.get("token")
    if not isinstance(jwt_token, str) or not jwt_token:
        print(
            f"FAIL: generateToken response missing JWTToken. Keys: {list(result.keys())}",
            file=sys.stderr,
        )
        return None

    return jwt_token


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Bot JWT from a running OpenMetadata instance.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("AI_SDK_HOST", DEFAULT_OM_URL),
        help=f"OpenMetadata server URL (default: {DEFAULT_OM_URL})",
    )
    parser.add_argument(
        "--expiry-days",
        type=int,
        default=30,
        help="Token expiry in days (default: 30; OM supports 7/30/60/90 or 0=Unlimited)",
    )
    parser.add_argument(
        "--username",
        default=DEFAULT_ADMIN_USERNAME,
        help=(
            "OM admin login identifier (default: admin; also retries "
            "admin@open-metadata.org on basic-auth installs)"
        ),
    )
    parser.add_argument(
        "--password",
        default="admin",
        help="OM admin password (default: admin)",
    )
    args = parser.parse_args()

    base_url = args.host.rstrip("/")
    expiry_value = _resolve_expiry(args.expiry_days)

    print(f"generate-bot-jwt: connecting to {base_url} ...")
    print()

    # Step 1: Health check
    print("[1/4] Checking OM health ...")
    if not check_health(base_url):
        print(
            "\nERROR: OpenMetadata is not reachable. Start it with: make om-start",
            file=sys.stderr,
        )
        return 1

    # Step 2: Admin login
    print(f"[2/4] Logging in as {args.username} ...")
    admin_token = login_admin(base_url, args.username, args.password)
    if admin_token is None:
        print(
            "\nERROR: Admin login failed. Check credentials "
            "(default: admin/admin; some installs require admin@open-metadata.org).",
            file=sys.stderr,
        )
        return 1
    print("  Login successful.")

    # Step 3: Find bot user
    print(f"[3/4] Looking up bot '{BOT_NAME}' ...")
    user_data = get_bot_user(base_url, admin_token)
    if user_data is None:
        return 1

    # Step 4: Generate token
    print(f"[4/4] Generating JWT with expiry={expiry_value} ...")
    jwt_token = generate_token(base_url, admin_token, user_data, expiry_value)
    if not jwt_token:
        print("\nERROR: Token generation failed.", file=sys.stderr)
        return 1

    # Print the token and instructions
    print()
    print("=" * 60)
    print("  Bot JWT generated successfully!")
    print("=" * 60)
    print()
    print("  Token (copy the line below into your .env):")
    print()
    print(f"  AI_SDK_TOKEN={jwt_token}")
    print()
    print("  Next steps:")
    print("    1. Open .env in your editor")
    print("    2. Replace the AI_SDK_TOKEN= line with the value above")
    print("    3. Run: python scripts/smoke_test.py --include-om")
    print()
    print("  SECURITY: Do NOT commit this token to git or paste it in GitHub.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
