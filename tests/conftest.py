import os
os.environ["TESTING"] = "1"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

from app.config import MONGO_URI, DATABASE_NAME
from app.database import set_db, get_db
from app.main import app
from app.routers.auth import hash_password, create_token


@pytest_asyncio.fixture
async def test_db():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    set_db(db)
    await db.users.delete_many({})
    await db.fields.delete_many({})
    await db.sensor_data.delete_many({})
    await db.decisions.delete_many({})
    await db.events.delete_many({})
    await db.settings.delete_many({})
    yield db
    await db.users.delete_many({})
    await db.fields.delete_many({})
    await db.sensor_data.delete_many({})
    await db.decisions.delete_many({})
    await db.events.delete_many({})
    await db.settings.delete_many({})
    client.close()


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_user(test_db):
    db = test_db
    user = {
        "username": "test_admin",
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "full_name": "مدیر تست",
        "phone": "09121111111",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    token = create_token(user_id, "admin")
    return {"user_id": user_id, "token": token, "username": "test_admin", "password": "admin123"}


@pytest_asyncio.fixture
async def farmer_user(test_db):
    db = test_db
    user = {
        "username": "test_farmer",
        "password_hash": hash_password("farmer123"),
        "role": "farmer",
        "full_name": "کشاورز تست",
        "phone": "09192222222",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    token = create_token(user_id, "farmer")
    return {"user_id": user_id, "token": token, "username": "test_farmer", "password": "farmer123"}


@pytest_asyncio.fixture
async def second_farmer_user(test_db):
    db = test_db
    user = {
        "username": "test_farmer2",
        "password_hash": hash_password("farmer123"),
        "role": "farmer",
        "full_name": "کشاورز تست دوم",
        "phone": "09193333333",
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    token = create_token(user_id, "farmer")
    return {"user_id": user_id, "token": token, "username": "test_farmer2", "password": "farmer123"}


@pytest_asyncio.fixture
async def sample_field(test_db, farmer_user):
    db = test_db
    field = {
        "owner_id": farmer_user["user_id"],
        "field_name": "مزرعه تست",
        "location": "تهران",
        "crop_type": "گندم",
        "area_hectares": 10.0,
        "notes": "یادداشت تست",
        "irrigation_schedule": "هر ۳ روز",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db.fields.insert_one(field)
    field_id = str(result.inserted_id)
    return {"field_id": field_id, **field}
