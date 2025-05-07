from datetime import timedelta

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_token,
)
from .config import settings
from .database import Base, engine, get_session
from .models import get_user, Task, User
from .schemas import (
    TaskCreate,
    TaskFilter,
    TaskResponse,
    UserCreate,
    UserBase,
    Token,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not getattr(app.state, 'testing', False):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/register", response_model=UserBase)
async def create_user(user_data: UserCreate, session=Depends(get_session)):
    if session.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if session.query(User).filter(User.name == user_data.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@app.post("/login", response_model=Token)
async def login_user(
    user_data: OAuth2PasswordRequestForm = Depends(),
    session=Depends(get_session),
):
    user = authenticate_user(user_data.username, user_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect name or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.name}, expires_delta=refresh_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
    }


@app.post("/refresh")
async def refresh_token(refresh_token: str, session=Depends(get_session)):
    token_data = verify_token(refresh_token)
    name = token_data.get("sub")

    user = get_user(session, name=name)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    new_access_token = create_access_token(
        data={"sub": user.name}, expires_delta=access_token_expires
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    existing_task = (
        session.query(Task)
        .filter(Task.title == task.title, Task.owner_id == current_user.id)
        .first()
    )
    if existing_task:
        raise HTTPException(
            status_code=400,
            detail="Task with this title already exists for this user",
        )

    task = Task(**task.model_dump(), owner_id=current_user.id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    offset: int = 0,
    limit: int = 100,
    filters: TaskFilter = Depends(),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = session.query(Task).filter(Task.owner_id == current_user.id)

    if filters.status:
        query = query.filter(Task.status == filters.status)

    if filters.priority:
        query = query.filter(Task.priority == filters.priority)

    if filters.created_after:
        query = query.filter(Task.created_at >= filters.created_after)

    if filters.created_before:
        next_day = filters.created_before + timedelta(days=1)
        query = query.filter(Task.created_at < next_day)

    return (
        query.order_by(Task.created_at.desc()).offset(offset).limit(limit).all()
    )


@app.get("/tasks/search", response_model=list[TaskResponse])
def search_tasks(
    q: str,
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    search = f"%{q}%"
    tasks = session.query(Task).filter(
        Task.owner_id == current_user.id,
        or_(
            Task.title.ilike(search),
            Task.description.ilike(search)
        )
    ).order_by(Task.created_at.desc()).offset(offset).limit(limit).all()

    if not tasks:
        raise HTTPException(
            status_code=404,
            detail="No tasks found matching your search"
        )
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    task = (
        session.query(Task)
        .filter(Task.id == task_id, Task.owner_id == current_user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()