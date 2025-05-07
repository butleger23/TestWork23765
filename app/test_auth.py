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
