from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_db
from app.models import AuthorizationCode, User
from app.services.client_service import get_client_by_client_id, verify_client_secret
from app.oidc.core import create_access_token, create_id_token
from app.oidc.claims import id_token_claims
from app.schemas import TokenResponse


router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def token(grant_type: str = Form(...), code: str = Form(None), redirect_uri: str = Form(None), client_id: str = Form(...), client_secret: str = Form(...), db: Session = Depends(get_db)):
  client = get_client_by_client_id(client_id)
  if not client or not verify_client_secret(client, client_secret):
    raise HTTPException(status_code=400, detail="invalid_client")
  if grant_type != "authorization_code":
    raise HTTPException(status_code=400, detail="unsupported_grant_type")
  auth_code = db.query(AuthorizationCode).filter(AuthorizationCode.code == code).first()
  if not auth_code or auth_code.client_id != client_id or auth_code.redirect_uri != redirect_uri or auth_code.expires_at < datetime.utcnow():
    raise HTTPException(status_code=400, detail="invalid_grant")
  user = db.query(User).filter(User.id == auth_code.user_id).first()
  access = create_access_token(sub=str(user.id), scope=auth_code.scope, aud=client_id)
  idt = create_id_token(sub=str(user.id), claims=id_token_claims(user, client_id), aud=client_id)
  db.delete(auth_code)
  db.commit()
  return {"access_token": access, "token_type": "Bearer", "expires_in": 3600, "id_token": idt, "scope": auth_code.scope}
