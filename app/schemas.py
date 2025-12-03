from pydantic import BaseModel


class UserCreate(BaseModel):
  username: str
  email: str
  password: str


class UserOut(BaseModel):
  id: int
  username: str
  email: str
  is_active: bool

  class Config:
    orm_mode = True


class ClientCreate(BaseModel):
  client_id: str
  client_secret: str
  redirect_uris: list[str]
  scopes: list[str]
  grant_types: list[str]
  response_types: list[str]


class TokenResponse(BaseModel):
  access_token: str
  token_type: str
  expires_in: int
  id_token: str | None = None
  scope: str | None = None


class UserInfoResponse(BaseModel):
  sub: str
  name: str | None = None
  email: str | None = None
