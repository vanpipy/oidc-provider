from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.infrastructure.auth.password import verify_password
from app.application.services.user_service import get_user_by_username
from app.application.services.client_service import validate_client_redirect_uri, get_client_by_client_id
from app.application.services.authorization_service import create_authorization_code


templates = Jinja2Templates(directory="app/api/web/templates")
router = APIRouter()


@router.get("/authorize")
def authorize(request: Request, response_type: str, client_id: str, redirect_uri: str, scope: str = "openid", state: str | None = None, db: Session = Depends(get_db)):
  if response_type != "code":
    raise HTTPException(status_code=400, detail="unsupported_response_type")
  client = get_client_by_client_id(db, client_id)
  if not client or not validate_client_redirect_uri(client, redirect_uri):
    raise HTTPException(status_code=400, detail="invalid_client")
  return templates.TemplateResponse("login.html", {"request": request, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state or ""})


@router.post("/authorize")
def authorize_login(request: Request, username: str = Form(...), password: str = Form(...), client_id: str = Form(...), redirect_uri: str = Form(...), scope: str = Form("") , state: str = Form("") , db: Session = Depends(get_db)):
  user = get_user_by_username(db, username)
  if not user or not verify_password(password, user.hashed_password):
    raise HTTPException(status_code=400, detail="access_denied")
  code = create_authorization_code(
    db=db,
    client_id=client_id,
    user_id=user.id,
    redirect_uri=redirect_uri,
    scope=scope,
  )
  url = f"{redirect_uri}?code={code.code}"
  if state:
    url = f"{url}&state={state}"
  return RedirectResponse(url, status_code=302)
