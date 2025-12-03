import time
import json
from typing import Any, Dict
from jose import jwt
from jose.utils import base64url_encode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from hashlib import sha256

from app.config import settings


ALGORITHM = "RS256"


class KeyStore:
  def __init__(self) -> None:
    self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = self._private_key.public_key()
    numbers = public_key.public_numbers()
    n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    thumb = sha256(n + e).hexdigest()[:16]
    self._kid = f"kid-{thumb}"

  def private_key(self):
    return self._private_key

  def kid(self) -> str:
    return self._kid

  def jwk(self) -> Dict[str, Any]:
    public_key = self._private_key.public_key()
    numbers = public_key.public_numbers()
    n = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")
    e = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")
    n_b64 = base64url_encode(n).decode()
    e_b64 = base64url_encode(e).decode()
    return {"kty": "RSA", "alg": ALGORITHM, "use": "sig", "kid": self._kid, "n": n_b64, "e": e_b64}


keystore = KeyStore()


def create_access_token(sub: str, scope: str | None, aud: str | None) -> str:
  now = int(time.time())
  payload = {
    "iss": settings.OIDC_ISSUER_URL,
    "sub": sub,
    "aud": aud or "",
    "iat": now,
    "exp": now + settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    "scope": scope or "",
  }
  token = jwt.encode(payload, keystore.private_key(), algorithm=ALGORITHM, headers={"kid": keystore.kid()})
  return token


def create_id_token(sub: str, claims: Dict[str, Any], aud: str) -> str:
  now = int(time.time())
  payload = {
    "iss": settings.OIDC_ISSUER_URL,
    "sub": sub,
    "aud": aud,
    "iat": now,
    "exp": now + settings.ID_TOKEN_EXPIRE_SECONDS,
    **claims,
  }
  token = jwt.encode(payload, keystore.private_key(), algorithm=ALGORITHM, headers={"kid": keystore.kid()})
  return token


def jwks() -> Dict[str, Any]:
  return {"keys": [keystore.jwk()]}


def decode_token(token: str) -> Dict[str, Any]:
  public_key = keystore.private_key().public_key()
  pem = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
  return jwt.decode(token, pem, algorithms=[ALGORITHM], audience=None, options={"verify_aud": False})
