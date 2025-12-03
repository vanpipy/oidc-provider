from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.endpoints.authorization import router as authorization_router
from app.endpoints.token import router as token_router
from app.endpoints.userinfo import router as userinfo_router
from app.endpoints.discovery import router as discovery_router
from app.endpoints.jwks import router as jwks_router
from app.services.user_service import create_user
from app.services.client_service import create_client
from app.models import User, Client


app = FastAPI(title=settings.PROJECT_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
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


app.include_router(authorization_router)
app.include_router(token_router)
app.include_router(userinfo_router)
app.include_router(discovery_router)
app.include_router(jwks_router)
