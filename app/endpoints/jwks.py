from fastapi import APIRouter
from app.oidc.core import jwks


router = APIRouter()


@router.get("/jwks")
def get_jwks():
  return jwks()
