from flask import Flask, render_template_string, session
import pytest
from app.csrf import (
    SESSION_ID_KEY,
    clear_csrf_token,
    csrf_protect,
    generate_csrf_token,
    get_cookie_security_config,
    init_csrf,
    validate_csrf_token,
)


def test_token_generation_and_persistence():
    mock_session = {}
    token1 = generate_csrf_token(mock_session)
    assert isinstance(token1, str)
    assert len(token1) >= 40
    assert generate_csrf_token(mock_session) == token1

    token2 = generate_csrf_token(mock_session, force_regenerate=True)
    assert token2 != token1


def test_token_uniqueness_across_sessions():
    tokens = {generate_csrf_token({}) for _ in range(50)}
    assert len(tokens) == 50


def test_valid_token_succeeds(monkeypatch):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    mock_session = {}
    token = generate_csrf_token(mock_session)
    assert validate_csrf_token(mock_session, token) is True


@pytest.mark.parametrize("bad_token", [None, "", "invalid_token", "a" * 43])
def test_missing_or_invalid_token_fails(monkeypatch, bad_token):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    mock_session = {}
    generate_csrf_token(mock_session)
    assert validate_csrf_token(mock_session, bad_token) is False


def test_another_sessions_token_fails(monkeypatch):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    alice_session = {}
    bob_session = {}

    alice_token = generate_csrf_token(alice_session)
    bob_token = generate_csrf_token(bob_session)

    assert validate_csrf_token(alice_session, bob_token) is False
    assert validate_csrf_token(alice_session, alice_token) is True


def test_clear_csrf_token_invalidates_session(monkeypatch):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    mock_session = {}
    token = generate_csrf_token(mock_session)
    clear_csrf_token(mock_session)
    assert validate_csrf_token(mock_session, token) is False


def test_cookie_security_config(monkeypatch):
    monkeypatch.setenv("SAMESITE_MODE", "Strict")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    config = get_cookie_security_config()
    assert config["SESSION_COOKIE_HTTPONLY"] is True
    assert config["SESSION_COOKIE_SAMESITE"] == "Strict"
    assert config["SESSION_COOKIE_SECURE"] is True


def test_flask_transfer_route_enforcement(monkeypatch):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("SAMESITE_MODE", "None")

    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    init_csrf(app)

    balances = {"alice": 1000, "bob": 500}

    @app.route("/token")
    def get_token():
        return generate_csrf_token(session)

    @app.route("/transfer", methods=["POST"])
    @csrf_protect
    def transfer():
        balances["alice"] -= 100
        balances["bob"] += 100
        return "Transfer complete", 200

    alice_client = app.test_client()
    bob_client = app.test_client()

    alice_token = alice_client.get("/token").get_data(as_text=True)
    bob_token = bob_client.get("/token").get_data(as_text=True)

    assert alice_client.post("/transfer", data={}).status_code == 403
    assert balances == {"alice": 1000, "bob": 500}

    assert alice_client.post("/transfer", data={"csrf_token": "wrong"}).status_code == 403
    assert balances == {"alice": 1000, "bob": 500}

    assert alice_client.post("/transfer", data={"csrf_token": bob_token}).status_code == 403
    assert balances == {"alice": 1000, "bob": 500}

    assert alice_client.post("/transfer", data={"csrf_token": alice_token}).status_code == 200
    assert balances == {"alice": 900, "bob": 600}


def test_force_regenerate_rotates_session_id_and_token(monkeypatch):
    monkeypatch.setenv("CSRF_ENABLED", "true")
    mock_session = {}
    token1 = generate_csrf_token(mock_session)
    sid1 = mock_session[SESSION_ID_KEY]

    token2 = generate_csrf_token(mock_session, force_regenerate=True)
    sid2 = mock_session[SESSION_ID_KEY]

    assert sid2 != sid1
    assert token2 != token1
    assert validate_csrf_token(mock_session, token1) is False
    assert validate_csrf_token(mock_session, token2) is True


def test_dashboard_transfer_form_includes_csrf_token():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    init_csrf(app)

    form_snippet = """
    <form method="POST" action="/transfer">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="text" name="receiver" placeholder="Send to (username)">
        <input type="number" step="0.01" name="amount" placeholder="Amount">
        <button type="submit">Send</button>
    </form>
    """
    with app.test_request_context("/dashboard"):
        rendered = render_template_string(form_snippet)
        assert 'name="csrf_token"' in rendered
        assert 'value=""' not in rendered