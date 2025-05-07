import enum

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

from .database import Base


class StatusEnum(enum.Enum):
    pending = 'pending'
    done = 'done'


class PriorityEnum(enum.Enum):
    high = 1
    medium = 2
    low = 3


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True)
    description = Column(String)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    priority = Column(Integer, default=PriorityEnum.medium.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey('user.id'))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    name = Column(String, unique=True)
    hashed_password = Column(String)
    services = relationship('Task', backref='owner')


def get_user(db: Session, name: str):
    return db.query(User).filter(User.name == name).first()