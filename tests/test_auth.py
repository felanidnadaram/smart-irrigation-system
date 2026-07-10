import pytest


@pytest.mark.asyncio
async def test_admin_login_success(client, admin_user):
    resp = await client.post("/auth/login", json={
        "username": admin_user["username"],
        "password": admin_user["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["full_name"] == "مدیر تست"


@pytest.mark.asyncio
async def test_farmer_login_success(client, farmer_user):
    resp = await client.post("/auth/login", json={
        "username": farmer_user["username"],
        "password": farmer_user["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "farmer"
    assert data["full_name"] == "کشاورز تست"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(client, admin_user):
    resp = await client.post("/auth/login", json={
        "username": admin_user["username"],
        "password": "wrong_password",
    })
    assert resp.status_code == 401
    data = resp.json()
    assert "نام کاربری یا رمز عبور اشتباه است" in data["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails(client):
    resp = await client.post("/auth/login", json={
        "username": "nonexistent_user",
        "password": "any_password",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client):
    resp = await client.post("/auth/register", json={
        "username": "new_farmer",
        "password": "pass123456",
        "full_name": "کشاورز جدید",
        "role": "farmer",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "new_farmer"
    assert data["role"] == "farmer"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username_fails(client, admin_user):
    resp = await client.post("/auth/register", json={
        "username": admin_user["username"],
        "password": "pass123456",
        "full_name": "تکراری",
        "role": "farmer",
    })
    assert resp.status_code == 400
    assert "نام کاربری قبلاً استفاده شده است" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_get_me_returns_current_user(client, farmer_user):
    resp = await client.get("/auth/me", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == farmer_user["username"]
    assert data["role"] == "farmer"


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(client):
    resp = await client.get("/auth/me", headers={
        "Authorization": "Bearer invalid.token.here"
    })
    assert resp.status_code == 401
    assert "توکن" in resp.json()["detail"]
