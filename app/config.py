from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  PROJECT_NAME: str = "Identity Provider"
  DEBUG: bool = False
  DATABASE_URL: str = "sqlite:///./app.db"
  SECRET_KEY: str = "changeme"
  OIDC_ISSUER_URL: str = "http://localhost:8000"
  ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
  ID_TOKEN_EXPIRE_SECONDS: int = 3600

  model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)


settings = Settings()
