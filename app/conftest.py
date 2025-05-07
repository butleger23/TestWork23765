import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .auth import get_password_hash
from .database import Base, get_session
from .main import app
from .models import PriorityEnum, StatusEnum, Task, User


SQLITE_DATABASE_URL = 'sqlite:///:memory:'


@pytest.fixture(scope="session")
def test_engine():
    """Session-wide test database engine"""
    engine = create_engine(
        SQLITE_DATABASE_URL,
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Creates a new database session for each test with rollback"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session):
    """Test client with dependency overrides and testing signal"""
    app.state.testing = True

    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    original_get_session = app.dependency_overrides.get(get_session)

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client

    app.state.testing = False
    if original_get_session is None:
        app.dependency_overrides.pop(get_session, None)
    else:
        app.dependency_overrides[get_session] = original_get_session


@pytest.fixture
def test_user(db_session):
    """Test user fixture"""
    user = User(
        email='test@example.com',
        name='testuser',
        hashed_password=get_password_hash('testpass'),
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_client(test_client, test_user):
    """Authenticated test client"""
    response = test_client.post(
        '/login', data={'username': test_user.name, 'password': 'testpass'}
    )
    token = response.json()['access_token']

    test_client.headers.update({'Authorization': f'Bearer {token}'})
    return test_client


@pytest.fixture
def test_task(db_session, test_user):
    """Fixture for creating a test task"""
    task_data = {
        'title': 'Test Task',
        'description': 'Test Description',
        'status': StatusEnum.pending,
        'priority': PriorityEnum.medium.value,
        'owner_id': test_user.id,
    }

    task = Task(**task_data)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
