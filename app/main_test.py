from .models import PriorityEnum, StatusEnum, Task, User


# Auth tests
def test_register_and_login(test_client):
    user_data = {
        'email': 'test@example.com',
        'name': 'testuser',
        'password': 'testpass',
    }
    response = test_client.post('/register', json=user_data)
    assert response.status_code == 200
    assert response.json()['email'] == user_data['email']

    login_data = {
        'username': user_data['name'],
        'password': user_data['password'],
    }
    response = test_client.post('/login', data=login_data)
    assert response.status_code == 200
    assert 'access_token' in response.json()


def test_login_invalid_credentials(test_client, test_user):
    login_data = {'username': test_user.name, 'password': 'wrongpassword'}
    response = test_client.post('/login', data=login_data)
    assert response.status_code == 401
    assert response.json()['detail'] == 'Incorrect name or password'


def test_protected_route_without_token(test_client, test_task):
    response = test_client.get(f'/tasks/{test_task.id}')
    assert response.status_code == 401


# Tasks tests
def test_create_task_success(auth_client):
    task_data = {
        'title': 'New Task',
        'description': 'Task description',
        'status': StatusEnum.pending.value,
        'priority': PriorityEnum.medium.value,
    }
    response = auth_client.post('/tasks', json=task_data)
    assert response.status_code == 200
    assert response.json()['title'] == task_data['title']


def test_get_task_success(auth_client, test_task):
    response = auth_client.get(f'/tasks/{test_task.id}')
    assert response.status_code == 200
    assert response.json()['id'] == test_task.id


def test_get_nonexistent_task(auth_client):
    response = auth_client.get('/tasks/999999')
    assert response.status_code == 404


def test_list_tasks_with_items(auth_client, test_task):
    response = auth_client.get('/tasks')
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_list_tasks_with_filters(auth_client):
    response = auth_client.get('/tasks?status=todo')
    assert response.status_code == 200
    assert all(task['status'] == 'todo' for task in response.json())


def test_search_tasks_found(auth_client, test_task):
    part_of_task_title = test_task.title[:4]
    response = auth_client.get(f'/tasks/search?q={part_of_task_title}')
    assert response.status_code == 200
    assert any(test_task.title in task['title'] for task in response.json())


def test_create_duplicate_task_title(auth_client, test_task):
    task_data = {
        'title': test_task.title,
        'description': 'Duplicate',
        'status': StatusEnum.pending.value,
        'priority': PriorityEnum.medium.value,
    }
    response = auth_client.post('/tasks', json=task_data)
    assert response.status_code == 400
    assert 'already exists' in response.json()['detail']


def test_get_another_users_task(auth_client, db_session):
    another_user = User(
        email='other@test.com', name='otheruser', hashed_password='hash'
    )
    db_session.add(another_user)
    db_session.commit()

    foreign_task = Task(title='Foreign', owner_id=another_user.id)
    db_session.add(foreign_task)
    db_session.commit()

    response = auth_client.get(f'/tasks/{foreign_task.id}')
    assert response.status_code == 404
