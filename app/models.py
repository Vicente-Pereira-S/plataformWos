from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String)
    role = Column(String, default="observador")
    is_active = Column(Boolean, default=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    group = relationship("Group", back_populates="users")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    code = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="group")
    alliances = relationship("Alliance", back_populates="group")

class Alliance(Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    slots = Column(Integer, default=0)
    group_id = Column(Integer, ForeignKey("groups.id"))

    group = relationship("Group", back_populates="alliances")
    candidates = relationship("Candidate", back_populates="alliance")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True)
    nickname = Column(String)
    speedups = Column(Integer)
    availability = Column(String)
    day = Column(Date)

    alliance_id = Column(Integer, ForeignKey("alliances.id"))
    alliance = relationship("Alliance", back_populates="candidates")
