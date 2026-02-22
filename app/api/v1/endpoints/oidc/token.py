from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.application.services.token_service import (
  issue_tokens_for_authorization_code,
  InvalidClientError,
  UnsupportedGrantTypeError,
  InvalidGrantError,
)
from app.api.v1.schemas.oidc import TokenResponse


router = APIRouter()


@router.post("/token", response_model=TokenResponse)
def token(grant_type: str = Form(...), code: str = Form(None), redirect_uri: str = Form(None), client_id: str = Form(...), client_secret: str = Form(...), db: Session = Depends(get_db)):
  try:
    access, idt, expires_in, scope = issue_tokens_for_authorization_code(
      db=db,
      grant_type=grant_type,
      code=code,
      redirect_uri=redirect_uri,
      client_id=client_id,
      client_secret=client_secret,
    )
  except InvalidClientError:
    raise HTTPException(status_code=400, detail="invalid_client")
  except UnsupportedGrantTypeError:
    raise HTTPException(status_code=400, detail="unsupported_grant_type")
  except InvalidGrantError:
    raise HTTPException(status_code=400, detail="invalid_grant")
  return {"access_token": access, "token_type": "Bearer", "expires_in": expires_in, "id_token": idt, "scope": scope}
