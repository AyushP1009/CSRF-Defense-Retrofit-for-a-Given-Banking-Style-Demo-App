from functools import wraps
import hmac
import os
import secrets
from typing import Dict, MutableMapping, Optional

SESSION_ID_KEY = "session_id"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Server-side synchronizer token registry: { session_id: csrf_token }
# Addresses Flask's default signed client-side cookie session behavior
_SERVER_TOKEN_STORE: Dict[str, str] = {}


def is_csrf_enabled() -> bool:
    """Toggle token enforcement via environment variable (defaults to True)."""
    return os.getenv("CSRF_ENABLED", "true").lower() in ("1", "true", "yes")


def get_samesite_policy() -> Optional[str]:
    """Return 'Strict', 'Lax', or None based on SAMESITE_MODE env var."""
    mode = os.getenv("SAMESITE_MODE", "Strict").strip()
    if mode.lower() in ("none", "off", "disabled", ""):
        return None
    return mode


def ensure_session_id(session_store: MutableMapping) -> str:
    """Ensure the current session has a unique server-tracked identifier."""
    if SESSION_ID_KEY not in session_store:
        session_store[SESSION_ID_KEY] = secrets.token_urlsafe(24)
    return session_store[SESSION_ID_KEY]


def generate_csrf_token(
    session_store: MutableMapping, force_regenerate: bool = False
) -> str:
    """Generate a 256-bit cryptographic token stored server-side and bound to the session ID."""
    if force_regenerate:
        clear_csrf_token(session_store)
        session_store[SESSION_ID_KEY] = secrets.token_urlsafe(24)

    sid = ensure_session_id(session_store)
    if force_regenerate or sid not in _SERVER_TOKEN_STORE:
        _SERVER_TOKEN_STORE[sid] = secrets.token_urlsafe(32)
    return _SERVER_TOKEN_STORE[sid]


def validate_csrf_token(
    session_store: MutableMapping, submitted_token: Optional[str]
) -> bool:
    """
    Validate a submitted token against the current session's server-side token.
    Returns True if CSRF is disabled or if tokens match in constant time.
    """
    if not is_csrf_enabled():
        return True

    if session_store.get("security_mode") == "vulnerable":
        return True

    sid = session_store.get(SESSION_ID_KEY)
    if not sid or not submitted_token or not isinstance(submitted_token, str):
        return False

    expected_token = _SERVER_TOKEN_STORE.get(sid)
    if not expected_token:
        return False

    return hmac.compare_digest(expected_token, submitted_token)


def clear_csrf_token(session_store: MutableMapping) -> None:
    """Remove server-side token on logout."""
    sid = session_store.get(SESSION_ID_KEY)
    if sid:
        _SERVER_TOKEN_STORE.pop(sid, None)


def get_cookie_security_config(
    samesite: Optional[str] = None, secure: Optional[bool] = None
) -> dict:
    """Return Flask session cookie configuration for hardened or relaxed demo modes."""
    resolved_samesite = (
        samesite if samesite is not None else get_samesite_policy()
    )
    resolved_secure = (
        secure
        if secure is not None
        else (os.getenv("COOKIE_SECURE", "false").lower() == "true")
    )
    return {
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": resolved_samesite,
        "SESSION_COOKIE_SECURE": resolved_secure,
    }


def init_csrf(app) -> None:
    """Register cookie config and Jinja2 {{ csrf_token() }} helper on a Flask app."""
    from flask import session

    app.config.update(get_cookie_security_config())

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": lambda: generate_csrf_token(session)}


def csrf_protect(view_func):
    """Decorator for state-changing POST routes (e.g., POST /transfer)."""
    from flask import abort, request, session

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        submitted = request.form.get(CSRF_FORM_FIELD) or request.headers.get(
            CSRF_HEADER_NAME
        )
        if not validate_csrf_token(session, submitted):
            abort(
                403,
                description="CSRF token missing, invalid, or mismatched for this session.",
            )
        return view_func(*args, **kwargs)

    return wrapped