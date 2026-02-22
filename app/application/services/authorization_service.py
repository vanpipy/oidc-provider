from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from app.infrastructure.database.models import AuthorizationCode
from app.domain.services.scope_rules import normalize_scope


def create_authorization_code(
  db: Session,
  client_id: str,
  user_id: int,
  redirect_uri: str,
  scope: str,
  expires_in_minutes: int = 5,
) -> AuthorizationCode:
  code_value = uuid.uuid4().hex
  normalized_scope = normalize_scope(scope)
  code = AuthorizationCode(
    code=code_value,
    client_id=client_id,
    user_id=user_id,
    redirect_uri=redirect_uri,
    scope=normalized_scope,
    expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
  )
  db.add(code)
  db.commit()
  db.refresh(code)
  return code
