def _signup(client, username="testuser", email="test@example.com", password="StrongPass123!"):
    return client.post(
        "/users/signup",
        json={"username": username, "email": email, "password": password},
    )


def test_signup_creates_user(client):
    response = _signup(client)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["content"]["username"] == "testuser"


def test_signup_rejects_duplicate_username(client):
    _signup(client)
    response = _signup(client, email="different@example.com")
    assert response.status_code == 400


def test_login_with_correct_credentials(client):
    _signup(client)
    response = client.post(
        "/auth/signin",
        json={"username": "testuser", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]["access_token"]
    assert body["content"]["refresh_token"]


def test_login_with_wrong_password_fails(client):
    _signup(client)
    response = client.post(
        "/auth/signin",
        json={"username": "testuser", "password": "wrong-password"},
    )
    assert response.status_code == 400


def test_profile_requires_authentication(client):
    response = client.get("/users/profile")
    assert response.status_code in (401, 403)  # depends on your get_current_user's auth scheme


def test_authenticated_profile_fetch(client):
    _signup(client)
    login = client.post(
        "/auth/signin",
        json={"username": "testuser", "password": "StrongPass123!"},
    )
    access_token = login.json()["content"]["access_token"]

    response = client.get(
        "/users/profile",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["content"]["username"] == "testuser"