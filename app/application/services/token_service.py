from datetime import datetime
from typing import Tuple

from sqlalchemy.orm import Session

from app.infrastructure.database.models import AuthorizationCode, User
from app.application.services.client_service import get_client_by_client_id, verify_client_secret
from app.infrastructure.auth.jwt import create_access_token, create_id_token
from app.domain.services.claims import id_token_claims


class InvalidClientError(Exception):
  pass


class UnsupportedGrantTypeError(Exception):
  pass


class InvalidGrantError(Exception):
  pass


def issue_tokens_for_authorization_code(
  db: Session,
  grant_type: str,
  code: str,
  redirect_uri: str,
  client_id: str,
  client_secret: str,
) -> Tuple[str, str, int, str]:
  client = get_client_by_client_id(db, client_id)
  if not client or not verify_client_secret(client, client_secret):
    raise InvalidClientError()
  if grant_type != "authorization_code":
    raise UnsupportedGrantTypeError()
  auth_code = db.query(AuthorizationCode).filter(AuthorizationCode.code == code).first()
  if not auth_code or auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri or auth_code.expires_at < datetime.utcnow():
    raise InvalidGrantError()
  user = db.query(User).filter(User.id == auth_code.user_id).first()
  access = create_access_token(sub=str(user.id), scope=auth_code.scope, aud=client_id)
  idt = create_id_token(sub=str(user.id), claims=id_token_claims(user, client_id), aud=client_id)
  db.delete(auth_code)
  db.commit()
  return access, idt, 3600, auth_code.scope

