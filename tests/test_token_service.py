from datetime import datetime, timedelta

from app.infrastructure.database.session import Base, engine, SessionLocal
from app.infrastructure.database.models import User, Client, AuthorizationCode
from app.application.services.user_service import create_user
from app.application.services.client_service import create_client
from app.application.services.authorization_service import create_authorization_code
from app.application.services.token_service import (
  issue_tokens_for_authorization_code,
  InvalidClientError,
  UnsupportedGrantTypeError,
  InvalidGrantError,
)
from app.infrastructure.auth.jwt import decode_token


def setup_db():
  Base.metadata.create_all(bind=engine)


def setup_demo_user_client_and_code():
  setup_db()
  db = SessionLocal()
  try:
    user = db.query(User).filter(User.username == "token-user").first()
    if not user:
      user = create_user(db, "token-user", "token-user@example.com", "demo1234")
    client = db.query(Client).filter(Client.client_id == "token-client").first()
    if not client:
      client = create_client(db, "token-client", "secret123", ["http://localhost:3000/callback"], ["openid"])
    code = create_authorization_code(
      db=db,
      client_id=client.client_id,
      user_id=user.id,
      redirect_uri="http://localhost:3000/callback",
      scope="openid",
      expires_in_minutes=5,
    )
    return user.id, client.client_id, code.code
  finally:
    db.close()


def test_issue_tokens_for_authorization_code_success():
  user_id, client_id, code_value = setup_demo_user_client_and_code()
  db = SessionLocal()
  try:
    access, idt, expires_in, scope = issue_tokens_for_authorization_code(
      db=db,
      grant_type="authorization_code",
      code=code_value,
      redirect_uri="http://localhost:3000/callback",
      client_id=client_id,
      client_secret="secret123",
    )
    assert expires_in == 3600
    assert scope == "openid"

    access_payload = decode_token(access)
    assert access_payload["sub"] == str(user_id)
    assert access_payload["aud"] == client_id

    id_payload = decode_token(idt)
    assert id_payload["sub"] == str(user_id)
    assert id_payload["aud"] == client_id

    remaining = db.query(AuthorizationCode).filter(AuthorizationCode.code == code_value).first()
    assert remaining is None
  finally:
    db.close()


def test_issue_tokens_invalid_client():
  user_id, client_id, code_value = setup_demo_user_client_and_code()
  db = SessionLocal()
  try:
    try:
      issue_tokens_for_authorization_code(
        db=db,
        grant_type="authorization_code",
        code=code_value,
        redirect_uri="http://localhost:3000/callback",
        client_id=client_id,
        client_secret="wrong-secret",
      )
      assert False
    except InvalidClientError:
      pass
  finally:
    db.close()


def test_issue_tokens_unsupported_grant_type():
  user_id, client_id, code_value = setup_demo_user_client_and_code()
  db = SessionLocal()
  try:
    try:
      issue_tokens_for_authorization_code(
        db=db,
        grant_type="password",
        code=code_value,
        redirect_uri="http://localhost:3000/callback",
        client_id=client_id,
        client_secret="secret123",
      )
      assert False
    except UnsupportedGrantTypeError:
      pass
  finally:
    db.close()


def test_issue_tokens_invalid_grant():
  user_id, client_id, code_value = setup_demo_user_client_and_code()
  db = SessionLocal()
  try:
    try:
      issue_tokens_for_authorization_code(
        db=db,
        grant_type="authorization_code",
        code="nonexistent-code",
        redirect_uri="http://localhost:3000/callback",
        client_id=client_id,
        client_secret="secret123",
      )
      assert False
    except InvalidGrantError:
      pass
  finally:
    db.close()
