from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_discovery():
  r = client.get("/.well-known/openid-configuration")
  assert r.status_code == 200
  data = r.json()
  assert "issuer" in data
  assert "authorization_endpoint" in data
  assert "jwks_uri" in data
