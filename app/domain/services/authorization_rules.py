from datetime import datetime

from app.infrastructure.database.models import AuthorizationCode


def is_authorization_code_valid_for_token(auth_code: AuthorizationCode, client_id: str, redirect_uri: str) -> bool:
  if not auth_code:
    return False
  if auth_code.client_id != client_id:
    return False
  if auth_code.redirect_uri != redirect_uri:
    return False
  if auth_code.expires_at < datetime.utcnow():
    return False
  return True

