import pytest
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_manual_sensor_generation_creates_reading(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]
    resp = await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "reading" in data
    reading = data["reading"]
    assert reading["field_id"] == field_id
    assert "soil_moisture" in reading
    assert "temperature" in reading
    assert "humidity" in reading
    assert "light_intensity" in reading


@pytest.mark.asyncio
async def test_latest_readings_returns_newest_reading(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]

    await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })

    resp = await client.get(f"/sensors/{field_id}/latest", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["field_id"] == field_id
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_historical_sensor_query_by_time_range(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]

    await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {farmer_user['token']}"
    })

    now = datetime.utcnow()
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()

    resp = await client.get(
        f"/sensors/{field_id}/history?start_time={start}&end_time={end}&limit=50",
        headers={"Authorization": f"Bearer {farmer_user['token']}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_farmer_cannot_generate_for_other_field(client, second_farmer_user, sample_field):
    field_id = sample_field["field_id"]
    resp = await client.post(f"/sensors/{field_id}/generate", headers={
        "Authorization": f"Bearer {second_farmer_user['token']}"
    })
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_historical_data_generation(client, farmer_user, sample_field):
    field_id = sample_field["field_id"]
    resp = await client.post(
        f"/sensors/{field_id}/generate-historical?days=2",
        headers={"Authorization": f"Bearer {farmer_user['token']}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "داده تاریخچه تولید شد" in data["message"]
