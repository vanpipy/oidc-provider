from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(50), unique=True, index=True)
  email = Column(String(255), unique=True, index=True)
  hashed_password = Column(String(255))
  is_active = Column(Boolean, default=True)
  created_at = Column(DateTime, default=datetime.utcnow)


class Client(Base):
  __tablename__ = "clients"
  id = Column(Integer, primary_key=True, index=True)
  client_id = Column(String(128), unique=True, index=True)
  client_secret = Column(String(255))
  redirect_uris = Column(Text)
  scopes = Column(Text)
  grant_types = Column(Text)
  response_types = Column(Text)
  created_at = Column(DateTime, default=datetime.utcnow)


class AuthorizationCode(Base):
  __tablename__ = "authorization_codes"
  id = Column(Integer, primary_key=True, index=True)
  code = Column(String(255), unique=True, index=True)
  client_id = Column(String(128), index=True)
  user_id = Column(Integer, ForeignKey("users.id"))
  redirect_uri = Column(Text)
  scope = Column(Text)
  expires_at = Column(DateTime)
  user = relationship("User")
