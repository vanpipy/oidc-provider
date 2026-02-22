import json
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import urlopen, Request, build_opener, HTTPErrorProcessor

import pytest
import uvicorn

from app.cli import seed_demo
from app.main import app


BASE_URL = "http://127.0.0.1:8001"


def _extract_code_and_state(location: str) -> tuple[str | None, str | None]:
  parsed = urlparse(location)
  params = parse_qs(parsed.query)
  code = params.get("code", [None])[0]
  state = params.get("state", [None])[0]
  return code, state


class _NoRedirect(HTTPErrorProcessor):
  def http_response(self, request, response):
    return response

  https_response = http_response


def _run_server() -> None:
  config = uvicorn.Config(app, host="127.0.0.1", port=8001, log_level="info")
  server = uvicorn.Server(config)
  server.run()


def _wait_for_server_ready(timeout_seconds: float = 30.0) -> None:
  deadline = time.time() + timeout_seconds
  url = f"{BASE_URL}/.well-known/openid-configuration"
  last_error: Exception | None = None
  while time.time() < deadline:
    try:
      response = urlopen(url, timeout=1.0)
      if response.getcode() < 500:
        return
      last_error = RuntimeError(f"unexpected status {response.getcode()}")
    except Exception as exc:
      last_error = exc
    time.sleep(0.5)
  if last_error is None:
    last_error = RuntimeError("server did not become ready in time")
  raise last_error


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
  seed_demo()


@pytest.fixture(scope="session")
def live_server() -> None:
  thread = threading.Thread(target=_run_server, daemon=True)
  thread.start()
  _wait_for_server_ready()
  yield


def test_s1_authorization_code_flow_success_blackbox(live_server: None) -> None:
  params = {
    "response_type": "code",
    "client_id": "demo-client",
    "redirect_uri": "http://localhost:3000/callback",
    "scope": "openid profile email",
    "state": "xyz",
  }
  query = urlencode(params)
  auth_url = f"{BASE_URL}/authorize?{query}"
  auth_response = urlopen(auth_url, timeout=5.0)
  assert auth_response.getcode() == 200

  login_body = urlencode(
    {
      "username": "demo",
      "password": "demo1234",
      "client_id": "demo-client",
      "redirect_uri": "http://localhost:3000/callback",
      "scope": "openid profile email",
      "state": "xyz",
    }
  ).encode()
  login_request = Request(
    f"{BASE_URL}/authorize",
    data=login_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
  )
  opener = build_opener(_NoRedirect())
  login_response = opener.open(login_request, timeout=5.0)
  assert login_response.getcode() == 302
  location = login_response.headers["Location"]
  code, state = _extract_code_and_state(location)
  assert code is not None
  assert state == "xyz"

  token_body = urlencode(
    {
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": "http://localhost:3000/callback",
      "client_id": "demo-client",
      "client_secret": "secret123",
    }
  ).encode()
  token_request = Request(
    f"{BASE_URL}/token",
    data=token_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
  )
  token_response = urlopen(token_request, timeout=5.0)
  assert token_response.getcode() == 200
  token_data = json.loads(token_response.read().decode())
  assert token_data["token_type"] == "Bearer"
  assert token_data["access_token"]
  assert token_data["id_token"]

  userinfo_request = Request(
    f"{BASE_URL}/userinfo",
    headers={"Authorization": f"Bearer {token_data['access_token']}"},
    method="GET",
  )
  userinfo_response = urlopen(userinfo_request, timeout=5.0)
  assert userinfo_response.getcode() == 200
  userinfo = json.loads(userinfo_response.read().decode())
  assert userinfo["sub"]
  assert userinfo["name"]
  assert "email" in userinfo


def test_s2_invalid_client_secret_blackbox(live_server: None) -> None:
  login_body = urlencode(
    {
      "username": "demo",
      "password": "demo1234",
      "client_id": "demo-client",
      "redirect_uri": "http://localhost:3000/callback",
      "scope": "openid",
      "state": "",
    }
  ).encode()
  login_request = Request(
    f"{BASE_URL}/authorize",
    data=login_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
  )
  opener = build_opener(_NoRedirect())
  login_response = opener.open(login_request, timeout=5.0)
  assert login_response.getcode() == 302
  location = login_response.headers["Location"]
  code, _ = _extract_code_and_state(location)
  assert code is not None

  token_body = urlencode(
    {
      "grant_type": "authorization_code",
      "code": code,
      "redirect_uri": "http://localhost:3000/callback",
      "client_id": "demo-client",
      "client_secret": "wrong-secret",
    }
  ).encode()
  token_request = Request(
    f"{BASE_URL}/token",
    data=token_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
  )
  try:
    token_response = urlopen(token_request, timeout=5.0)
    status_code = token_response.getcode()
    body = json.loads(token_response.read().decode())
  except HTTPError as error:
    status_code = error.code
    body = json.loads(error.read().decode())
  assert status_code == 400
  assert body["detail"] == "invalid_client"


def test_s3_invalid_grant_nonexistent_code_blackbox(live_server: None) -> None:
  token_body = urlencode(
    {
      "grant_type": "authorization_code",
      "code": "nonexistent-code",
      "redirect_uri": "http://localhost:3000/callback",
      "client_id": "demo-client",
      "client_secret": "secret123",
    }
  ).encode()
  token_request = Request(
    f"{BASE_URL}/token",
    data=token_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
  )
  try:
    token_response = urlopen(token_request, timeout=5.0)
    status_code = token_response.getcode()
    body = json.loads(token_response.read().decode())
  except HTTPError as error:
    status_code = error.code
    body = json.loads(error.read().decode())
  assert status_code == 400
  assert body["detail"] == "invalid_grant"

