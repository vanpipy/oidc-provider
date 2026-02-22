from sqlalchemy.orm import Session

from app.infrastructure.database.models import User
from app.infrastructure.auth.jwt import decode_token
from app.domain.services.claims import userinfo_claims


class InvalidTokenError(Exception):
  pass


def get_userinfo_from_token(db: Session, token: str):
  try:
    payload = decode_token(token)
  except Exception:
    raise InvalidTokenError()
  user_id = payload.get("sub")
  if not user_id:
    raise InvalidTokenError()
  user = db.query(User).filter(User.id == int(user_id)).first()
  if not user:
    raise InvalidTokenError()
  return userinfo_claims(user)

