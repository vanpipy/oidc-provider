from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from app.infrastructure.database.models import AuthorizationCode


def create_authorization_code(
  db: Session,
  client_id: str,
  user_id: int,
  redirect_uri: str,
  scope: str,
  expires_in_minutes: int = 5,
) -> AuthorizationCode:
  code_value = uuid.uuid4().hex
  code = AuthorizationCode(
    code=code_value,
    client_id=client_id,
    user_id=user_id,
    redirect_uri=redirect_uri,
    scope=scope,
    expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
  )
  db.add(code)
  db.commit()
  db.refresh(code)
  return code

