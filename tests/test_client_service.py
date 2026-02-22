import uuid

from app.infrastructure.database.session import Base, engine, SessionLocal
from app.application.services.client_service import (
  create_client,
  get_client_by_client_id,
  validate_client_redirect_uri,
  verify_client_secret,
)


def setup_db():
  Base.metadata.create_all(bind=engine)


def test_create_and_get_client_by_client_id():
  setup_db()
  db = SessionLocal()
  try:
    client_id = f"test-client-{uuid.uuid4().hex}"
    redirect_uri = "http://localhost/callback"
    scopes = ["openid", "profile"]
    client = create_client(db, client_id, "secret123", [redirect_uri], scopes)
    fetched = get_client_by_client_id(db, client_id)
    assert fetched is not None
    assert fetched.id == client.id
    assert fetched.client_id == client_id
    assert verify_client_secret(fetched, "secret123")
    assert validate_client_redirect_uri(fetched, redirect_uri)
  finally:
    db.close()


def test_validate_client_redirect_uri_false_for_unknown_uri():
  setup_db()
  db = SessionLocal()
  try:
    client_id = f"test-client-{uuid.uuid4().hex}"
    redirect_uri = "http://localhost/callback"
    client = create_client(db, client_id, "secret123", [redirect_uri], ["openid"])
    assert not validate_client_redirect_uri(client, "http://localhost/other")
  finally:
    db.close()

