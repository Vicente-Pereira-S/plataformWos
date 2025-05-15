from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

# ------------------------------
# MODELO DE USUARIO
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True) # No se usa, es para desactivar cuenta si algun dia lo quiero hacer
    last_login = Column(DateTime, default=func.now())
    secret_question = Column(String, nullable=True)
    secret_answer = Column(String, nullable=True)

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
    alliances = relationship("Alliance", back_populates="group", cascade="all, delete-orphan")
    days = relationship("GroupDay", back_populates="group", cascade="all, delete-orphan")


# ------------------------------
# MODELO DE MIEMBRO DEL GRUPO 
# ------------------------------
class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")


# ------------------------------
# MODELO DE ALIANZA DEL GRUPO
# ------------------------------
class Alliance(Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    name = Column(String(3), nullable=False)
    limit = Column(Integer, nullable=True)

    group = relationship("Group", back_populates="alliances")
    submissions = relationship("UserSubmission", back_populates="alliance", cascade="all, delete-orphan")


# ------------------------------
# MODELO DE DÍA ORGANIZADO POR EL GRUPO
# ------------------------------
class GroupDay(Base):
    __tablename__ = "group_days"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    name = Column(String, nullable=False)  # Ej: "VP Monday"

    group = relationship("Group", back_populates="days")
    submissions = relationship("UserSubmission", back_populates="group_day", cascade="all, delete-orphan")
    assignments = relationship("GroupAssignment", back_populates="group_day", cascade="all, delete-orphan")



# ------------------------------
# MODELO DE ENVÍO ANÓNIMO DE INFORMACIÓN
# ------------------------------
class UserSubmission(Base):
    __tablename__ = "user_submissions"

    id = Column(Integer, primary_key=True, index=True)
    group_day_id = Column(Integer, ForeignKey("group_days.id"))
    alliance_id = Column(Integer, ForeignKey("alliances.id"))
    nickname = Column(String, nullable=False)
    ingame_id = Column(String, nullable=True)
    speedups = Column(Integer, nullable=False)

    group_day = relationship("GroupDay", back_populates="submissions")
    alliance = relationship("Alliance", back_populates="submissions")
    availability = relationship("AvailabilitySlot", back_populates="submission", cascade="all, delete-orphan")


# ------------------------------
# MODELO DE HORARIOS DISPONIBLES (por envío)
# ------------------------------
class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("user_submissions.id"))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    submission = relationship("UserSubmission", back_populates="availability")



# ------------------------------
# MODELO DE ASIGNACIONES GUARDADAS
# ------------------------------
class GroupAssignment(Base):
    __tablename__ = "group_assignments"

    id = Column(Integer, primary_key=True, index=True)
    group_day_id = Column(Integer, ForeignKey("group_days.id"))
    hour_block = Column(Integer, nullable=False)  # De 0 a 47
    nickname = Column(String, nullable=False)
    ingame_id = Column(String, nullable=True)
    alliance = Column(String(3), nullable=False)
    speedups = Column(Integer, nullable=False)
    availability_str = Column(String, nullable=False)

    group_day = relationship("GroupDay", back_populates="assignments")
