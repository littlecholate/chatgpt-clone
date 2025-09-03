from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    email = Column(String(75), nullable=False, unique=True)
    password = Column(String(250), nullable=False)