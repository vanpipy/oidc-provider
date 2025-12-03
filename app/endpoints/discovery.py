from fastapi import APIRouter
from app.config import settings


router = APIRouter()


@router.get("/.well-known/openid-configuration")
def discovery():
  return {
    "issuer": settings.OIDC_ISSUER_URL,
    "authorization_endpoint": f"{settings.OIDC_ISSUER_URL}/authorize",
    "token_endpoint": f"{settings.OIDC_ISSUER_URL}/token",
    "userinfo_endpoint": f"{settings.OIDC_ISSUER_URL}/userinfo",
    "jwks_uri": f"{settings.OIDC_ISSUER_URL}/jwks",
    "response_types_supported": ["code"],
    "grant_types_supported": ["authorization_code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
    "scopes_supported": ["openid", "profile", "email"],
  }
