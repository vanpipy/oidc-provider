from typing import Dict, Any
from datetime import datetime, timezone

from app.config import settings
from app.models import User


def id_token_claims(user: User, client_id: str) -> Dict[str, Any]:
  return {
    "name": user.username,
    "email": user.email,
  }


def userinfo_claims(user: User) -> Dict[str, Any]:
  return {
    "sub": str(user.id),
    "name": user.username,
    "email": user.email,
  }
