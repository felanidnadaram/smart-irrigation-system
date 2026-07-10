import pytest


@pytest.mark.asyncio
async def test_farmer_cannot_access_admin_endpoint(client, farmer_user):
    resp = await client.get("/dashboard/admin/stats", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 403
    assert "مدیران" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_admin_can_access_stats(client, admin_user):
    resp = await client.get("/dashboard/admin/stats", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_fields" in data
    assert "total_readings" in data


@pytest.mark.asyncio
async def test_admin_can_manage_users(client, admin_user, farmer_user):
    resp = await client.get("/dashboard/admin/users", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    users = resp.json()
    usernames = [u["username"] for u in users]
    assert farmer_user["username"] in usernames


@pytest.mark.asyncio
async def test_admin_can_update_global_thresholds(client, admin_user):
    resp = await client.put("/dashboard/admin/thresholds", json={
        "soil_moisture_low": 25.0,
        "temperature_high": 38.0,
    }, headers={"Authorization": f"Bearer {admin_user['token']}"})
    assert resp.status_code == 200
    assert "آستانه‌ها" in resp.json()["message"]


@pytest.mark.asyncio
async def test_admin_can_list_all_fields(client, admin_user, sample_field):
    resp = await client.get("/dashboard/admin/fields", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    fields = resp.json()
    assert len(fields) >= 1
    field_names = [f["field_name"] for f in fields]
    assert "مزرعه تست" in field_names


@pytest.mark.asyncio
async def test_admin_can_list_decisions(client, admin_user, sample_field):
    field_id = sample_field["field_id"]
    await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })

    resp = await client.get("/dashboard/admin/decisions", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_admin_can_view_events(client, admin_user):
    resp = await client.get("/dashboard/admin/events", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_admin_cannot_delete_own_account(client, admin_user):
    resp = await client.delete(f"/dashboard/admin/users/{admin_user['user_id']}", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 400
    assert "خود را حذف" in resp.json()["detail"]
