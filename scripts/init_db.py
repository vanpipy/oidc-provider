from app.database import Base, engine, SessionLocal
from app.services.user_service import create_user
from app.services.client_service import create_client


def main():
  Base.metadata.create_all(bind=engine)
  db = SessionLocal()
  try:
    create_user(db, "admin", "admin@example.com", "admin1234")
    create_client(db, "client", "secret123", ["http://localhost:3000/callback"], ["openid", "profile", "email"])
  finally:
    db.close()


if __name__ == "__main__":
    main()
