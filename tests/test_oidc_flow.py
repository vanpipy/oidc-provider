from urllib.parse import urlparse, parse_qs

from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.database.session import Base, engine, SessionLocal
from app.infrastructure.database.models import User, Client
from app.application.services.user_service import create_user
from app.application.services.client_service import create_client


def _extract_code_and_state(location: str) -> tuple[str, str | None]:
  parsed = urlparse(location)
  params = parse_qs(parsed.query)
  code = params.get("code", [None])[0]
  state = params.get("state", [None])[0]
  return code, state


def _setup_demo_user_and_client():
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
      create_user(db, "demo", "demo@example.com", "demo1234")
    client = db.query(Client).filter(Client.client_id == "demo-client").first()
    if not client:
      create_client(db, "demo-client", "secret123", ["http://localhost:3000/callback"], ["openid", "profile", "email"])
  finally:
    db.close()


def _obtain_authorization_code(client: TestClient, redirect_uri: str, scope: str, state: str):
  login_response = client.post(
    "/authorize",
    data={
      "username": "demo",
      "password": "demo1234",
      "client_id": "demo-client",
      "redirect_uri": redirect_uri,
      "scope": scope,
      "state": state,
    },
  )
  redirect_response = login_response.history[-1] if login_response.history else login_response
  location = redirect_response.headers["location"]
  return _extract_code_and_state(location)


def test_authorization_code_flow_success():
  _setup_demo_user_and_client()
  client = TestClient(app)

  redirect_uri = "http://localhost:3000/callback"
  auth_response = client.get(
    "/authorize",
    params={
      "response_type": "code",
      "client_id": "demo-client",
      "redirect_uri": redirect_uri,
      "scope": "openid profile email",
      "state": "xyz",
    },
  )
  assert auth_response.status_code == 200

  login_response = client.post(
    "/authorize",
    data={
      "username": "demo",
      "password": "demo1234",
      "client_id": "demo-client",
      "redirect_uri": redirect_uri,
      "scope": "openid profile email",
      "state": "xyz",
    },
  )
  redirect_response = login_response.history[-1] if login_response.history else login_response
  assert redirect_response.status_code == 302
  location = redirect_response.headers["location"]
  code, state = _extract_code_and_state(location)
  assert code is not None
  assert state == "xyz"

  token_response = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": redirect_uri,
      "client_id": "demo-client",
      "client_secret": "secret123",
    },
  )
  assert token_response.status_code == 200
  token_data = token_response.json()
  assert token_data["token_type"] == "Bearer"
  assert token_data["access_token"]
  assert token_data["id_token"]

  userinfo_response = client.get(
    "/userinfo",
    headers={"Authorization": f"Bearer {token_data['access_token']}"},
  )
  assert userinfo_response.status_code == 200
  userinfo = userinfo_response.json()
  assert userinfo["sub"]
  assert userinfo["name"]
  assert "email" in userinfo


def test_token_endpoint_invalid_client_secret():
  _setup_demo_user_and_client()
  client = TestClient(app)

  redirect_uri = "http://localhost:3000/callback"
  code, _ = _obtain_authorization_code(client, redirect_uri, "openid", "")
  assert code is not None

  token_response = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": redirect_uri,
      "client_id": "demo-client",
      "client_secret": "wrong-secret",
    },
  )
  assert token_response.status_code == 400
  assert token_response.json()["detail"] == "invalid_client"


def test_token_endpoint_invalid_grant_nonexistent_code():
  _setup_demo_user_and_client()
  client = TestClient(app)

  redirect_uri = "http://localhost:3000/callback"
  token_response = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": "nonexistent-code",
      "redirect_uri": redirect_uri,
      "client_id": "demo-client",
      "client_secret": "secret123",
    },
  )
  assert token_response.status_code == 400
  assert token_response.json()["detail"] == "invalid_grant"


def test_token_endpoint_invalid_grant_reused_code():
  _setup_demo_user_and_client()
  client = TestClient(app)

  redirect_uri = "http://localhost:3000/callback"
  code, _ = _obtain_authorization_code(client, redirect_uri, "openid", "")
  token_response = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": redirect_uri,
      "client_id": "demo-client",
      "client_secret": "secret123",
    },
  )
  assert token_response.status_code == 200

  token_response2 = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": redirect_uri,
      "client_id": "demo-client",
      "client_secret": "secret123",
    },
  )
  assert token_response2.status_code == 400
  assert token_response2.json()["detail"] == "invalid_grant"


def test_token_endpoint_invalid_grant_redirect_uri_mismatch():
  _setup_demo_user_and_client()
  client = TestClient(app)

  correct_redirect = "http://localhost:3000/callback"
  code, _ = _obtain_authorization_code(client, correct_redirect, "openid", "")

  bad_redirect = "http://localhost:3000/other"
  token_response = client.post(
    "/token",
    data={
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": bad_redirect,
      "client_id": "demo-client",
      "client_secret": "secret123",
    },
  )
  assert token_response.status_code == 400
  assert token_response.json()["detail"] == "invalid_grant"


def test_authorize_invalid_response_type():
  _setup_demo_user_and_client()
  client = TestClient(app)

  redirect_uri = "http://localhost:3000/callback"
  resp = client.get(
    "/authorize",
    params={
      "response_type": "token",
      "client_id": "demo-client",
      "redirect_uri": redirect_uri,
      "scope": "openid",
      "state": "xyz",
    },
  )
  assert resp.status_code == 400
  assert resp.json()["detail"] == "unsupported_response_type"


def test_authorize_invalid_client_or_redirect_uri():
  _setup_demo_user_and_client()
  client = TestClient(app)

  resp = client.get(
    "/authorize",
    params={
      "response_type": "code",
      "client_id": "unknown-client",
      "redirect_uri": "http://localhost:3000/callback",
      "scope": "openid",
      "state": "xyz",
    },
  )
  assert resp.status_code == 400
  assert resp.json()["detail"] == "invalid_client"

  resp = client.get(
    "/authorize",
    params={
      "response_type": "code",
      "client_id": "demo-client",
      "redirect_uri": "http://localhost:3000/other",
      "scope": "openid",
      "state": "xyz",
    },
  )
  assert resp.status_code == 400
  assert resp.json()["detail"] == "invalid_client"


def test_userinfo_missing_authorization_header():
  _setup_demo_user_and_client()
  client = TestClient(app)

  resp = client.get("/userinfo")
  assert resp.status_code == 401
  assert resp.json()["detail"] == "invalid_token"


def test_userinfo_invalid_token():
  _setup_demo_user_and_client()
  client = TestClient(app)

  resp = client.get(
    "/userinfo",
    headers={"Authorization": "Bearer not-a-valid-token"},
  )
  assert resp.status_code == 401
  assert resp.json()["detail"] == "invalid_token"

