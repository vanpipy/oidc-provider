from datetime import datetime, timedelta

from app.infrastructure.database.session import Base, engine, SessionLocal
from app.infrastructure.database.models import User, Client, AuthorizationCode
from app.application.services.user_service import create_user
from app.application.services.client_service import create_client
from app.application.services.authorization_service import create_authorization_code


def setup_db():
  Base.metadata.create_all(bind=engine)


def test_create_authorization_code_persists_record_and_sets_expiry():
  setup_db()
  db = SessionLocal()
  try:
    user = db.query(User).filter(User.username == "demo-auth").first()
    if not user:
      user = create_user(db, "demo-auth", "demo-auth@example.com", "demo1234")
    client = db.query(Client).filter(Client.client_id == "demo-auth-client").first()
    if not client:
      client = create_client(db, "demo-auth-client", "secret123", ["http://localhost:3000/callback"], ["openid"])

    before = datetime.utcnow()
    code = create_authorization_code(
      db=db,
      client_id=client.client_id,
      user_id=user.id,
      redirect_uri="http://localhost:3000/callback",
      scope="openid",
      expires_in_minutes=10,
    )
    after = datetime.utcnow()

    assert code.id is not None
    assert code.code
    assert code.client_id == client.client_id
    assert code.user_id == user.id
    assert code.redirect_uri == "http://localhost:3000/callback"
    assert code.scope == "openid"
    assert before + timedelta(minutes=10) <= code.expires_at <= after + timedelta(minutes=10)

    stored = db.query(AuthorizationCode).filter(AuthorizationCode.code == code.code).first()
    assert stored is not None
    assert stored.id == code.id
  finally:
    db.close()
