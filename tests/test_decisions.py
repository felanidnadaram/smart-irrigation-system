import pytest
from app.services.decisions import analyze_and_decide


@pytest.mark.asyncio
async def test_low_soil_moisture_creates_irrigation_recommendation():
    sensor_data = {
        "soil_moisture": 20.0,
        "temperature": 25.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    irrigation = [d for d in decisions if d["decision_type"] == "irrigation"]
    assert len(irrigation) >= 1
    assert irrigation[0]["priority"] == "high"
    assert "آبیاری" in irrigation[0]["title"]
    assert irrigation[0]["sensor_value"] == 20.0


@pytest.mark.asyncio
async def test_critical_low_moisture_creates_critical_priority():
    sensor_data = {
        "soil_moisture": 10.0,
        "temperature": 25.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    irrigation = [d for d in decisions if d["decision_type"] == "irrigation"]
    assert len(irrigation) >= 1
    assert irrigation[0]["priority"] == "critical"


@pytest.mark.asyncio
async def test_high_temperature_creates_alert():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 40.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    temp_alerts = [d for d in decisions if d["decision_type"] == "temperature_alert"]
    assert len(temp_alerts) >= 1
    assert "دمای بالا" in temp_alerts[0]["title"]
    assert temp_alerts[0]["sensor_value"] == 40.0


@pytest.mark.asyncio
async def test_critical_high_temperature():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 45.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    temp_alerts = [d for d in decisions if d["decision_type"] == "temperature_alert"]
    assert len(temp_alerts) >= 1
    assert temp_alerts[0]["priority"] == "critical"


@pytest.mark.asyncio
async def test_low_temperature_creates_alert():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 2.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    temp_alerts = [d for d in decisions if d["decision_type"] == "temperature_alert"]
    assert len(temp_alerts) >= 1
    assert "دمای پایین" in temp_alerts[0]["title"]


@pytest.mark.asyncio
async def test_high_humidity_creates_alert():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 25.0,
        "humidity": 95.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    humidity_alerts = [d for d in decisions if d["decision_type"] == "humidity_alert"]
    assert len(humidity_alerts) >= 1
    assert "رطوبت بالای هوا" in humidity_alerts[0]["title"]


@pytest.mark.asyncio
async def test_low_humidity_creates_alert():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 25.0,
        "humidity": 15.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    humidity_alerts = [d for d in decisions if d["decision_type"] == "humidity_alert"]
    assert len(humidity_alerts) >= 1
    assert "رطوبت پایین هوا" in humidity_alerts[0]["title"]


@pytest.mark.asyncio
async def test_high_light_intensity_creates_alert():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 25.0,
        "humidity": 50.0,
        "light_intensity": 95000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    light_alerts = [d for d in decisions if d["decision_type"] == "light_alert"]
    assert len(light_alerts) >= 1
    assert "شدت نور بالا" in light_alerts[0]["title"]


@pytest.mark.asyncio
async def test_normal_values_produce_no_decisions():
    sensor_data = {
        "soil_moisture": 50.0,
        "temperature": 25.0,
        "humidity": 55.0,
        "light_intensity": 40000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    assert len(decisions) == 0


@pytest.mark.asyncio
async def test_custom_thresholds_are_respected():
    sensor_data = {
        "soil_moisture": 25.0,
        "temperature": 30.0,
        "humidity": 50.0,
        "light_intensity": 40000,
    }
    custom_thresholds = {
        "soil_moisture_low": 20.0,
        "soil_moisture_high": 80.0,
        "temperature_high": 35.0,
        "temperature_low": 5.0,
        "humidity_low": 20.0,
        "humidity_high": 90.0,
        "light_intensity_high": 90000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data, thresholds=custom_thresholds)
    irrigation = [d for d in decisions if d["decision_type"] == "irrigation"]
    assert len(irrigation) == 0


@pytest.mark.asyncio
async def test_multiple_alerts_for_worst_case():
    sensor_data = {
        "soil_moisture": 5.0,
        "temperature": 50.0,
        "humidity": 5.0,
        "light_intensity": 100000,
    }
    decisions = await analyze_and_decide("field_1", sensor_data)
    assert len(decisions) >= 4
    types = {d["decision_type"] for d in decisions}
    assert "irrigation" in types
    assert "temperature_alert" in types
    assert "humidity_alert" in types
    assert "light_alert" in types
