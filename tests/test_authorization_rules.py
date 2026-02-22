from datetime import datetime, timedelta

from app.infrastructure.database.models import AuthorizationCode
from app.domain.services.authorization_rules import is_authorization_code_valid_for_token
from app.domain.services.scope_rules import normalize_scope


def _build_auth_code(client_id: str = "demo-client", redirect_uri: str = "http://localhost:3000/callback", expires_delta: int = 60):
  now = datetime.utcnow()
  auth_code = AuthorizationCode(
    client_id=client_id,
    user_id=1,
    code="test-code",
    redirect_uri=redirect_uri,
    scope="openid",
    expires_at=now + timedelta(seconds=expires_delta),
  )
  return auth_code


def test_is_authorization_code_valid_for_token_success():
  auth_code = _build_auth_code()
  assert is_authorization_code_valid_for_token(auth_code, "demo-client", "http://localhost:3000/callback")


def test_is_authorization_code_valid_for_token_none():
  assert not is_authorization_code_valid_for_token(None, "demo-client", "http://localhost:3000/callback")


def test_is_authorization_code_valid_for_token_client_mismatch():
  auth_code = _build_auth_code(client_id="other-client")
  assert not is_authorization_code_valid_for_token(auth_code, "demo-client", "http://localhost:3000/callback")


def test_is_authorization_code_valid_for_token_redirect_uri_mismatch():
  auth_code = _build_auth_code(redirect_uri="http://localhost:3000/other")
  assert not is_authorization_code_valid_for_token(auth_code, "demo-client", "http://localhost:3000/callback")


def test_is_authorization_code_valid_for_token_expired():
  auth_code = _build_auth_code(expires_delta=-60)
  assert not is_authorization_code_valid_for_token(auth_code, "demo-client", "http://localhost:3000/callback")


def test_normalize_scope_defaults_to_openid_when_empty():
  assert normalize_scope("") == "openid"
  assert normalize_scope(None) == "openid"


def test_normalize_scope_keeps_existing_and_appends_missing_openid():
  assert normalize_scope("openid profile") == "openid profile"
  assert normalize_scope("profile") == "profile openid"


def test_normalize_scope_removes_duplicates_and_trims_spaces():
  assert normalize_scope("openid  openid  profile  ") == "openid profile"
