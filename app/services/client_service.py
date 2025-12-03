from typing import List
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Client
from app.auth import verify_password, hash_password


def get_client_by_client_id(client_id: str) -> Client | None:
  db = SessionLocal()
  try:
    return db.query(Client).filter(Client.client_id == client_id).first()
  finally:
    db.close()


def create_client(db: Session, client_id: str, client_secret: str, redirect_uris: List[str], scopes: List[str]) -> Client:
  client = Client(
    client_id=client_id,
    client_secret=hash_password(client_secret),
    redirect_uris=",".join(redirect_uris),
    scopes=",".join(scopes),
    grant_types="authorization_code",
    response_types="code",
  )
  db.add(client)
  db.commit()
  db.refresh(client)
  return client


def validate_client_redirect_uri(client: Client, uri: str) -> bool:
  uris = (client.redirect_uris or "").split(",")
  return uri in uris


def verify_client_secret(client: Client, secret: str) -> bool:
  return verify_password(secret, client.client_secret)
