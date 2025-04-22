from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


# ------------------------------
# MODELO DE USUARIO
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="observador")
    is_active = Column(Boolean, default=True)

    groups = relationship("GroupMember", back_populates="user")


# ------------------------------
# MODELO DE GRUPO
# ------------------------------
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    state_number = Column(Integer, nullable=False)
    group_code = Column(String, unique=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User", backref="created_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    # Placeholder para futuras relaciones como alliances, schedule, etc.


# ------------------------------
# MODELO DE MIEMBRO DEL GRUPO
# ------------------------------
class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    role = Column(String, default="member")  # "admin" o "member"

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")
