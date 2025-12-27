"""
LinkedIn OAuth helpers for the Streamlit frontend.

This module provides helpers to:
- build the LinkedIn authorization URL (stores `state` in session)
- exchange an authorization `code` for an access token
- fetch simple profile/email data after obtaining a token

Notes:
- For security, exchanging the authorization code for a token is ideally
  done on a backend (so the client secret is not leaked). This module
  supports two modes:
    1) If `LINKEDIN_TOKEN_EXCHANGE_URL` env var is set, the frontend will
       POST the `code` and `state` to that backend URL and expect JSON
       response with at least `access_token`.
    2) Otherwise (dev mode) the frontend will exchange directly with
       LinkedIn using `LINKEDIN_CLIENT_SECRET` (not recommended for prod).

Environment variables used (frontend):
- LINKEDIN_CLIENT_ID
- LINKEDIN_CLIENT_SECRET (optional; only for direct exchange)
- LINKEDIN_REDIRECT_URI
- LINKEDIN_TOKEN_EXCHANGE_URL (optional; backend endpoint to exchange code)

Session state keys (uses `frontend.session_state`):
- `linkedin_auth_state` -> the random state string
- `access_token` -> saved access token returned from LinkedIn or backend

Usage:
    from frontend import linkedin_auth as la
    url = la.build_auth_url()
    # open url for user to login; after redirect, get `code` and `state`
    token = la.exchange_code_for_token(code, state)
    profile = la.fetch_profile()
"""

from __future__ import annotations

import os
import secrets
import urllib.parse
from typing import Dict, Optional, Any

import requests

from st_helpers.session_state import SessionStateManager

S = SessionStateManager()

# LinkedIn endpoints
_AUTH_BASE = "https://www.linkedin.com/oauth/v2/authorization"
_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_PROFILE_URL = "https://api.linkedin.com/v2/me"
_EMAIL_URL = "https://api.linkedin.com/v2/emailAddress"

# env-configured values
CLIENT_ID = os.getenv("s")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8501/")

# Optional backend URL to handle secure token exchange
BACKEND_TOKEN_EXCHANGE = os.getenv("LINKEDIN_TOKEN_EXCHANGE_URL")

# default scopes (lite profile + email)
DEFAULT_SCOPE = "r_liteprofile r_emailaddress"


def _make_state() -> str:
    return secrets.token_urlsafe(16)


def build_auth_url(scope: Optional[str] = None, redirect_uri: Optional[str] = None) -> str:
    """Build the LinkedIn authorization URL and store `state` in session.

    Returns the URL the user should visit to authorize the app.
    """
    scope = scope or DEFAULT_SCOPE
    redirect_uri = redirect_uri or REDIRECT_URI

    if not CLIENT_ID:
        raise RuntimeError("LINKEDIN_CLIENT_ID not set in environment")

    state = _make_state()
    S.set_one(S.LINKEDIN_AUTH_STATE, state)
    S.set_one(S.LINKEDIN_REDIRECT_URI, redirect_uri)

    query = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
    }
    return f"{_AUTH_BASE}?{urllib.parse.urlencode(query)}"


def _backend_exchange(code: str, state: str) -> Dict[str, Any]:
    """Call a backend endpoint to exchange the code for a token.

    The backend is expected to accept JSON payload {code, state, redirect_uri}
    and return JSON with at least `access_token` on success.
    """
    if not BACKEND_TOKEN_EXCHANGE:
        raise RuntimeError("BACKEND_TOKEN_EXCHANGE not configured")

    payload = {"code": code, "state": state, "redirect_uri": S.get(S.LINKEDIN_REDIRECT_URI)}
    resp = requests.post(BACKEND_TOKEN_EXCHANGE, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _direct_exchange(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange code for token directly with LinkedIn (dev only).

    This requires `CLIENT_SECRET` to be present in env. Not recommended
    for production because the secret is present in the frontend.
    """
    if not CLIENT_SECRET:
        raise RuntimeError("LINKEDIN_CLIENT_SECRET not set for direct exchange")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(_TOKEN_URL, data=data, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def exchange_code_for_token(code: str, state: str) -> Dict[str, Any]:
    """Exchange the authorization `code` for an access token.

    Verifies `state` matches the one stored in session. If
    `LINKEDIN_TOKEN_EXCHANGE_URL` is set, delegates to that endpoint; else
    does a direct exchange with LinkedIn (requires `LINKEDIN_CLIENT_SECRET`).

    On success, stores `access_token` in session state and returns the raw
    token response dict.
    """
    init_state = S.get(S.LINKEDIN_AUTH_STATE)
    if not init_state or state != init_state:
        raise RuntimeError("OAuth state mismatch")

    redirect_uri = S.get(S.LINKEDIN_REDIRECT_URI) or REDIRECT_URI
    if BACKEND_TOKEN_EXCHANGE:
        token_resp = _backend_exchange(code, state)
    else:
        token_resp = _direct_exchange(code, redirect_uri)

    access_token = token_resp.get("access_token")
    if not access_token:
        raise RuntimeError(f"No access_token in token response: {token_resp}")

    # save token to session
    S.set_one(S.LINKEDIN_ACCESS_TOKEN, access_token)

    # clear auth state
    try:
        S.set_one(S.LINKEDIN_AUTH_STATE, None)
    except Exception:
        pass

    return token_resp


def _auth_headers() -> Dict[str, str]:
    """Build authorization headers using the saved access token."""
    token = S.get(S.LINKEDIN_ACCESS_TOKEN)
    if not token:
        raise RuntimeError("No access token in session; call exchange_code_for_token first")
    return {"Authorization": f"Bearer {token}", "X-Restli-Protocol-Version": "2.0.0"}


def fetch_profile() -> Dict[str, Any]:
    """Fetch basic LinkedIn profile and email (if token exists).

    Returns a dict with `profile` and `email` keys.
    """
    headers = _auth_headers()

    profile = {}
    email = None

    # fetch profile
    resp = requests.get(_PROFILE_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    profile = resp.json()

    # fetch email
    params = {"q": "members", "projection": "(elements*(handle~))"}
    resp2 = requests.get(_EMAIL_URL, headers=headers, params=params, timeout=15)
    resp2.raise_for_status()
    email_resp = resp2.json()
    # extract email if present
    try:
        elements = email_resp.get("elements", [])
        if elements and isinstance(elements, list):
            email = elements[0].get("handle~", {}).get("emailAddress")
    except Exception:
        email = None

    return {"profile": profile, "email": email}


def clear_linkedin_session() -> None:
    """Clear LinkedIn-related session state."""
    S.set_one(S.LINKEDIN_AUTH_STATE, None)
    S.set_one(S.LINKEDIN_REDIRECT_URI, None)
    S.set_one(S.LINKEDIN_ACCESS_TOKEN, None)