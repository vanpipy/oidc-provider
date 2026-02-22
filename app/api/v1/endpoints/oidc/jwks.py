from fastapi import APIRouter
from app.infrastructure.auth.jwt import jwks


router = APIRouter()


@router.get("/jwks")
def get_jwks():
  return jwks()
