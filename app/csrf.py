from functools import wraps
import hmac
import secrets
from typing import Dict, MutableMapping, Optional

from flask import session

SESSION_ID_KEY = "session_id"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

SECURE_MODE = "protected"
VULNERABLE_MODE = "vulnerable"

# Server-side synchronizer token registry:
# { session_id: csrf_token }
_SERVER_TOKEN_STORE: Dict[str, str] = {}


def security_enabled() -> bool:
    """
    Returns True when the current user's
    security mode is set to protected.
    """
    return (
        session.get(
            "security_mode",
            VULNERABLE_MODE,
        )
        == SECURE_MODE
    )


def is_csrf_enabled() -> bool:
    """
    CSRF protection follows
    the current security mode.
    """
    return security_enabled()


def ensure_session_id(
    session_store: MutableMapping,
) -> str:
    """
    Ensure the session has
    a unique identifier.
    """
    if SESSION_ID_KEY not in session_store:
        session_store[SESSION_ID_KEY] = (
            secrets.token_urlsafe(24)
        )

    return session_store[SESSION_ID_KEY]


def generate_csrf_token(
    session_store: MutableMapping,
    force_regenerate: bool = False,
) -> str:
    """
    Generate a CSRF token tied
    to the current session.
    """

    if force_regenerate:
        clear_csrf_token(session_store)
        session_store[SESSION_ID_KEY] = (
            secrets.token_urlsafe(24)
        )

    sid = ensure_session_id(session_store)

    if (
        force_regenerate
        or sid not in _SERVER_TOKEN_STORE
    ):
        _SERVER_TOKEN_STORE[sid] = (
            secrets.token_urlsafe(32)
        )

    return _SERVER_TOKEN_STORE[sid]


def validate_csrf_token(
    session_store: MutableMapping,
    submitted_token: Optional[str],
) -> bool:
    """
    Validate submitted token against
    the token stored on the server.
    """

    print(
        "DEBUG security_mode =",
        session.get("security_mode")
    )

    print(
        "DEBUG csrf_enabled =",
        is_csrf_enabled()
    )

    print(
        "DEBUG submitted_token =",
        submitted_token
    )

    # Vulnerable mode bypasses CSRF
    if not is_csrf_enabled():
        return True

    sid = session_store.get(
        SESSION_ID_KEY
    )

    if not sid:
        print("DEBUG no session id")
        return False

    if not submitted_token:
        print("DEBUG no submitted token")
        return False

    if not isinstance(
        submitted_token,
        str,
    ):
        print(
            "DEBUG submitted token not string"
        )
        return False

    expected_token = (
        _SERVER_TOKEN_STORE.get(sid)
    )

    print(
        "DEBUG expected_token =",
        expected_token
    )

    if not expected_token:
        print("DEBUG no expected token")
        return False

    if not isinstance(
        expected_token,
        str,
    ):
        print(
            "DEBUG expected token not string"
        )
        return False

    return hmac.compare_digest(
        expected_token,
        submitted_token,
    )


def clear_csrf_token(
    session_store: MutableMapping,
) -> None:
    """
    Remove the server-side token.
    """

    sid = session_store.get(
        SESSION_ID_KEY
    )

    if sid:
        _SERVER_TOKEN_STORE.pop(
            sid,
            None,
        )


def init_csrf(app) -> None:
    """
    Register csrf_token()
    for Jinja templates.
    """

    from flask import session

    @app.context_processor
    def inject_csrf_token():
        return {
            "csrf_token": (
                lambda: generate_csrf_token(
                    session
                )
            )
        }


def csrf_protect(view_func):
    """
    Protect state-changing routes.
    """

    from flask import (
        abort,
        request,
        session,
    )

    @wraps(view_func)
    def wrapped(*args, **kwargs):

        print(
            "CSRF_PROTECT EXECUTED"
        )

        print(
            request.form
        )

        submitted = (
            request.form.get(
                CSRF_FORM_FIELD
            )
            or request.headers.get(
                CSRF_HEADER_NAME
            )
        )

        if not validate_csrf_token(
            session,
            submitted,
        ):
            abort(
                403,
                description=(
                    "CSRF token missing, "
                    "invalid, or mismatched "
                    "for this session."
                ),
            )

        return view_func(
            *args,
            **kwargs,
        )

    return wrapped