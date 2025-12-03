from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth import get_db
from app.models import User
from app.oidc.core import decode_token
from app.oidc.claims import userinfo_claims


router = APIRouter()
bearer = HTTPBearer(auto_error=False)


@router.get("/userinfo")
def userinfo(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
  if credentials is None:
    raise HTTPException(status_code=401, detail="invalid_token")
  payload = decode_token(credentials.credentials)
  user_id = payload.get("sub")
  user = db.query(User).filter(User.id == int(user_id)).first()
  if not user:
    raise HTTPException(status_code=401, detail="invalid_token")
  return userinfo_claims(user)
