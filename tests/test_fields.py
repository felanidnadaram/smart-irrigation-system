import pytest


@pytest.mark.asyncio
async def test_farmer_can_create_field(client, farmer_user):
    resp = await client.post("/fields/", json={
        "field_name": "مزرعه جدید",
        "location": "اصفهان",
        "crop_type": "برنج",
        "area_hectares": 5.0,
        "notes": "تست ایجاد",
        "irrigation_schedule": "روزانه",
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_name"] == "مزرعه جدید"
    assert data["crop_type"] == "برنج"
    assert data["owner_id"] == farmer_user["user_id"]


@pytest.mark.asyncio
async def test_farmer_can_list_own_fields(client, farmer_user, sample_field):
    resp = await client.get("/fields/", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    field_ids = [f["id"] for f in data]
    assert sample_field["field_id"] in field_ids


@pytest.mark.asyncio
async def test_farmer_can_update_own_field(client, farmer_user, sample_field):
    resp = await client.put(f"/fields/{sample_field['field_id']}", json={
        "field_name": "مزرعه بروزرسانی شده",
        "crop_type": "جو",
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_name"] == "مزرعه بروزرسانی شده"
    assert data["crop_type"] == "جو"


@pytest.mark.asyncio
async def test_farmer_cannot_update_other_farmer_field(client, second_farmer_user, sample_field):
    resp = await client.put(f"/fields/{sample_field['field_id']}", json={
        "field_name": "تلاش برای دسترسی غیرمجاز",
    }, headers={"Authorization": f"Bearer {second_farmer_user['token']}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_farmer_can_delete_own_field(client, farmer_user, sample_field):
    resp = await client.delete(f"/fields/{sample_field['field_id']}", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    assert "حذف شد" in resp.json()["message"]

    resp2 = await client.get("/fields/", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    field_ids = [f["id"] for f in resp2.json()]
    assert sample_field["field_id"] not in field_ids


@pytest.mark.asyncio
async def test_farmer_cannot_access_other_farmer_field(client, second_farmer_user, sample_field):
    resp = await client.get(f"/fields/{sample_field['field_id']}", headers={
        "Authorization": f"Bearer {second_farmer_user['token']}"
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_farmer_cannot_list_fields_without_auth(client):
    resp = await client.get("/fields/")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_farmer_update_empty_body_fails(client, farmer_user, sample_field):
    resp = await client.put(f"/fields/{sample_field['field_id']}", json={
        "field_name": None,
        "crop_type": None,
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})
    assert resp.status_code == 400
    assert "بروزرسانی" in resp.json()["detail"]
