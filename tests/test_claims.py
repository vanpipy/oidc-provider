from dataclasses import dataclass

from app.domain.services.claims import id_token_claims, userinfo_claims


@dataclass
class DummyUser:
  id: int
  username: str
  email: str | None


def test_id_token_claims_uses_username_and_email():
  user = DummyUser(id=1, username="alice", email="alice@example.com")
  claims = id_token_claims(user, "client-1")
  assert claims["name"] == "alice"
  assert claims["email"] == "alice@example.com"


def test_userinfo_claims_includes_sub_and_optional_email():
  user = DummyUser(id=2, username="bob", email=None)
  claims = userinfo_claims(user)
  assert claims["sub"] == "2"
  assert claims["name"] == "bob"
  assert "email" in claims
  assert claims["email"] is None

