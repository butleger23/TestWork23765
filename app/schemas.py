from datetime import date, datetime
from typing import Union

from pydantic import BaseModel, EmailStr, Field

from .models import PriorityEnum, StatusEnum


class TaskBase(BaseModel):
    title: str
    description: Union[str, None] = None
    status: StatusEnum = StatusEnum.pending
    priority: int = PriorityEnum.medium

    class Config:
        use_enum_values = True


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Union[str, None] = None
    description: Union[str, None] = None
    status: Union[StatusEnum, None] = None
    priority: Union[int, None] = None


class TaskFilter(BaseModel):
    status: Union[str, None] = None
    priority: Union[int, None] = None
    created_after: Union[date, None] = Field(
        None,
        description="Filter tasks created after this date (YYYY-MM-DD)"
    )
    created_before: Union[date, None] = Field(
        None,
        description="Filter tasks created before this date (YYYY-MM-DD)"
    )


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    name: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    name: str