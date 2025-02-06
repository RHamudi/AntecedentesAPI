from pydantic import EmailStr
from sqlalchemy import Column, Integer, String
from ..config.postgress import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String, unique=False, index=True)
    