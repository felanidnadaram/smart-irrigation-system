import pytest
from datetime import datetime, timedelta
from app.services.sensor_generator import generate_sensor_reading
from app.services.decisions import create_decisions_from_readings, get_field_decisions
from app.database import get_db


@pytest.mark.asyncio
async def test_create_field_and_generate_sensor_data(client, farmer_user):
    create_resp = await client.post("/fields/", json={
        "field_name": "مزرعه جریان کامل",
        "location": "شیراز",
        "crop_type": "انگور",
        "area_hectares": 8.0,
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})
    assert create_resp.status_code == 200
    field_id = create_resp.json()["id"]

    gen_resp = await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert gen_resp.status_code == 200
    reading = gen_resp.json()["reading"]
    assert reading["field_id"] == field_id

    latest_resp = await client.get(f"/sensors/{field_id}/latest", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert latest_resp.status_code == 200
    assert latest_resp.json()["field_id"] == field_id


@pytest.mark.asyncio
async def test_decisions_stored_and_retrievable(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]

    gen_resp = await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert gen_resp.status_code == 200

    dec_resp = await client.get(f"/decisions/{field_id}", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert dec_resp.status_code == 200
    assert isinstance(dec_resp.json(), list)


@pytest.mark.asyncio
async def test_threshold_change_affects_decisions(test_db):
    db = test_db
    field_id = "test_field_threshold"
    sensor_data = {
        "soil_moisture": 25.0,
        "temperature": 30.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }

    from app.config import THRESHOLDS
    decisions_normal = await analyze_and_decide(field_id, sensor_data, THRESHOLDS)
    irrigation_normal = [d for d in decisions_normal if d["decision_type"] == "irrigation"]
    assert len(irrigation_normal) >= 1

    low_thresholds = {**THRESHOLDS, "soil_moisture_low": 20.0}
    decisions_low = await analyze_and_decide(field_id, sensor_data, low_thresholds)
    irrigation_low = [d for d in decisions_low if d["decision_type"] == "irrigation"]
    assert len(irrigation_low) == 0


@pytest.mark.asyncio
async def test_farmer_field_ownership_integrity(client, farmer_user, second_farmer_user):
    create_resp = await client.post("/fields/", json={
        "field_name": "مزرعه مالکیت",
        "location": "تبریز",
        "crop_type": "سیب",
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})
    field_id = create_resp.json()["id"]

    list_resp = await client.get("/fields/", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    my_ids = [f["id"] for f in list_resp.json()]
    assert field_id in my_ids

    other_list = await client.get("/fields/", headers={
        "Authorization": f"Bearer {second_farmer_user['token']}"
    })
    other_ids = [f["id"] for f in other_list.json()]
    assert field_id not in other_ids


@pytest.mark.asyncio
async def test_recommendations_endpoint_returns_expected_decisions(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]

    await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })

    resp = await client.get(f"/decisions/{field_id}", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    decisions = resp.json()
    for d in decisions:
        assert "decision_type" in d
        assert "title" in d
        assert "description" in d
        assert "recommended_action" in d


@pytest.mark.asyncio
async def test_admin_generate_all_fields(client, admin_user, farmer_user):
    await client.post("/fields/", json={
        "field_name": "مزرعه تست generate-all",
        "location": "قم",
        "crop_type": "enchilada",
    }, headers={"Authorization": f"Bearer {farmer_user['token']}"})

    resp = await client.post("/dashboard/admin/generate-all", headers={
        "Authorization": f"Bearer {admin_user['token']}"
    })
    assert resp.status_code == 200
    assert "تولید شد" in resp.json()["message"]


from app.services.decisions import analyze_and_decide
