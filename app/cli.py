import os
import json
import uvicorn

from app.database import Base, engine, SessionLocal
from app.services.user_service import create_user, get_user_by_username
from app.services.client_service import create_client, get_client_by_client_id
from app.models import User, Client
from app.oidc.core import jwks
from app.config import settings


def dev():
  uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)


def serve():
  uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)


def init_db():
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    if not db.query(User).filter(User.username == "admin").first():
      create_user(db, "admin", "admin@example.com", "admin1234")
    if not db.query(Client).filter(Client.client_id == "client").first():
      create_client(db, "client", "secret123", ["http://localhost:3000/callback"], ["openid", "profile", "email"])
  finally:
    db.close()


def drop_db():
  Base.metadata.drop_all(bind=engine)


def reset_db():
  drop_db()
  init_db()


def seed_demo():
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    if not db.query(User).filter(User.username == "demo").first():
      create_user(db, "demo", "demo@example.com", "demo1234")
    if not db.query(Client).filter(Client.client_id == "demo-client").first():
      create_client(db, "demo-client", "secret123", ["http://localhost:3000/callback"], ["openid", "profile", "email"])
  finally:
    db.close()


def create_user_cmd():
  username = os.getenv("USERNAME")
  email = os.getenv("EMAIL")
  password = os.getenv("PASSWORD")
  if not username or not email or not password:
    print("set USERNAME, EMAIL, PASSWORD")
    return
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    if get_user_by_username(db, username):
      print("user exists")
      return
    create_user(db, username, email, password)
    print("user created")
  finally:
    db.close()


def create_client_cmd():
  client_id = os.getenv("CLIENT_ID")
  client_secret = os.getenv("CLIENT_SECRET")
  redirect_uris = os.getenv("REDIRECT_URIS", "").split(",") if os.getenv("REDIRECT_URIS") else []
  scopes = os.getenv("SCOPES", "").split(",") if os.getenv("SCOPES") else []
  if not client_id or not client_secret or not redirect_uris or not scopes:
    print("set CLIENT_ID, CLIENT_SECRET, REDIRECT_URIS, SCOPES")
    return
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    if get_client_by_client_id(client_id):
      print("client exists")
      return
    create_client(db, client_id, client_secret, redirect_uris, scopes)
    print("client created")
  finally:
    db.close()


def print_jwks():
  print(json.dumps(jwks()))


def test():
  import pytest
  raise SystemExit(pytest.main(["-q"]))


def print_settings():
  print(json.dumps({
    "PROJECT_NAME": settings.PROJECT_NAME,
    "DEBUG": settings.DEBUG,
    "DATABASE_URL": settings.DATABASE_URL,
    "OIDC_ISSUER_URL": settings.OIDC_ISSUER_URL,
    "ACCESS_TOKEN_EXPIRE_SECONDS": settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    "ID_TOKEN_EXPIRE_SECONDS": settings.ID_TOKEN_EXPIRE_SECONDS,
  }))
