from sqlalchemy.orm import Session

from app.infrastructure.database.models import AuthorizationCode, User
from app.application.services.client_service import get_client_by_client_id, verify_client_secret
from app.infrastructure.auth.jwt import create_access_token, create_id_token
from app.domain.services.claims import id_token_claims
from app.domain.services.authorization_rules import is_authorization_code_valid_for_token


class InvalidClientError(Exception):
  pass


class UnsupportedGrantTypeError(Exception):
  pass


class InvalidGrantError(Exception):
  pass


class TokenSet:
  def __init__(self, access_token: str, id_token: str, expires_in: int, scope: str):
    self.access_token = access_token
    self.id_token = id_token
    self.expires_in = expires_in
    self.scope = scope


def issue_tokens_for_authorization_code(
  db: Session,
  grant_type: str,
  code: str,
  redirect_uri: str,
  client_id: str,
  client_secret: str,
) -> TokenSet:
  client = get_client_by_client_id(db, client_id)
  if not client or not verify_client_secret(client, client_secret):
    raise InvalidClientError()
  if grant_type != "authorization_code":
    raise UnsupportedGrantTypeError()
  auth_code = db.query(AuthorizationCode).filter(AuthorizationCode.code == code).first()
  if not is_authorization_code_valid_for_token(auth_code, client_id, redirect_uri):
    raise InvalidGrantError()
  user = db.query(User).filter(User.id == auth_code.user_id).first()
  access = create_access_token(sub=str(user.id), scope=auth_code.scope, aud=client_id)
  idt = create_id_token(sub=str(user.id), claims=id_token_claims(user, client_id), aud=client_id)
  db.delete(auth_code)
  db.commit()
  return TokenSet(access_token=access, id_token=idt, expires_in=3600, scope=auth_code.scope)
