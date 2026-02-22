from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.userinfo_service import get_userinfo_from_token, InvalidTokenError


router = APIRouter()
bearer = HTTPBearer(auto_error=False)


@router.get("/userinfo")
def userinfo(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
  if credentials is None:
    raise HTTPException(status_code=401, detail="invalid_token")
  try:
    return get_userinfo_from_token(db, credentials.credentials)
  except InvalidTokenError:
    raise HTTPException(status_code=401, detail="invalid_token")
