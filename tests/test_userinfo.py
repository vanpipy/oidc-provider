from app.infrastructure.database.session import Base, engine, SessionLocal
from app.infrastructure.database.models import User
from app.application.services.user_service import create_user
from app.application.services.userinfo_service import get_userinfo_from_token, InvalidTokenError
from app.infrastructure.auth.jwt import create_access_token


def setup_db():
  Base.metadata.create_all(bind=engine)


def setup_demo_user():
  setup_db()
  db = SessionLocal()
  try:
    user = db.query(User).filter(User.username == "userinfo-user").first()
    if not user:
      user = create_user(db, "userinfo-user", "userinfo-user@example.com", "demo1234")
    return user.id
  finally:
    db.close()


def test_get_userinfo_from_token_success():
  user_id = setup_demo_user()
  db = SessionLocal()
  try:
    token = create_access_token(sub=str(user_id), scope="openid", aud="userinfo-client")
    claims = get_userinfo_from_token(db, token)
    assert claims["sub"] == str(user_id)
    assert claims["name"] == "userinfo-user"
    assert "email" in claims
  finally:
    db.close()


def test_get_userinfo_from_token_invalid_token_raises_error():
  setup_demo_user()
  db = SessionLocal()
  try:
    try:
      get_userinfo_from_token(db, "not-a-valid-token")
      assert False
    except InvalidTokenError:
      pass
  finally:
    db.close()


def test_get_userinfo_from_token_unknown_user_raises_error():
  setup_demo_user()
  db = SessionLocal()
  try:
    token = create_access_token(sub="999999", scope="openid", aud="userinfo-client")
    try:
      get_userinfo_from_token(db, token)
      assert False
    except InvalidTokenError:
      pass
  finally:
    db.close()

