from typing import Dict, Any, Protocol


class ClaimsUser(Protocol):
  id: int
  username: str
  email: str | None


def id_token_claims(user: ClaimsUser, client_id: str) -> Dict[str, Any]:
  return {
    "name": user.username,
    "email": user.email,
  }
def userinfo_claims(user: ClaimsUser) -> Dict[str, Any]:
  return {
    "sub": str(user.id),
    "name": user.username,
    "email": user.email,
  }
