


async def test_register_success(client):
    response = await client.post(
        "/auth/register",
        json={"email": "newuser@test.com", "password": "parola123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "id" in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(client):
    payload = {"email": "duplicate@test.com", "password": "parola123"}
    await client.post("/auth/register", json=payload)
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 409


async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"email": "loginuser@test.com", "password": "parola123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "loginuser@test.com", "password": "parola123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"email": "wrongpass@test.com", "password": "parola123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "wrongpass@test.com", "password": "parolagresita"},
    )
    assert response.status_code == 401


async def test_login_nonexistent_user(client):
    response = await client.post(
        "/auth/login",
        data={"username": "nuexist@test.com", "password": "orice"},
    )
    assert response.status_code == 401

async def test_refresh_token_success(client):
    await client.post(
        "/auth/register",
        json={"email": "refreshuser@test.com", "password": "parola123"},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": "refreshuser@test.com", "password": "parola123"},
    )
    old_refresh = login_resp.json()["refresh_token"]

    response = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["refresh_token"] != old_refresh  

async def test_logout_revokes_refresh_token(client):
    await client.post(
        "/auth/register",
        json={"email": "logoutuser@test.com", "password": "parola123"},
    )
    login_resp = await client.post(
        "/auth/login",
        data={"username": "logoutuser@test.com", "password": "parola123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = await client.post("/auth/logout", json={"refresh_token": refresh_token})
    assert logout_resp.status_code == 204

    reuse_resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_resp.status_code == 401