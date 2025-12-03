from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_db, verify_password
from app.services.user_service import get_user_by_username
from app.services.client_service import validate_client_redirect_uri, get_client_by_client_id
from app.models import AuthorizationCode


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/authorize")
def authorize(request: Request, response_type: str, client_id: str, redirect_uri: str, scope: str = "", state: str | None = None):
  client = get_client_by_client_id(client_id)
  if not client or not validate_client_redirect_uri(client, redirect_uri):
    raise HTTPException(status_code=400, detail="invalid_client")
  return templates.TemplateResponse("login.html", {"request": request, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state or ""})


@router.post("/authorize")
def authorize_login(request: Request, username: str = Form(...), password: str = Form(...), client_id: str = Form(...), redirect_uri: str = Form(...), scope: str = Form("") , state: str = Form("") , db: Session = Depends(get_db)):
  user = get_user_by_username(db, username)
  if not user or not verify_password(password, user.hashed_password):
    raise HTTPException(status_code=400, detail="access_denied")
  code_value = uuid.uuid4().hex
  code = AuthorizationCode(
    code=code_value,
    client_id=client_id,
    user_id=user.id,
    redirect_uri=redirect_uri,
    scope=scope,
    expires_at=datetime.utcnow() + timedelta(minutes=5),
  )
  db.add(code)
  db.commit()
  db.refresh(code)
  url = f"{redirect_uri}?code={code_value}"
  if state:
    url = f"{url}&state={state}"
  return RedirectResponse(url, status_code=302)
