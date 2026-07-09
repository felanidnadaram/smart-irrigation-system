from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URI, DATABASE_NAME

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    await db.users.create_index("username", unique=True)
    await db.users.create_index("role")
    await db.fields.create_index("owner_id")
    await db.sensor_data.create_index([("field_id", 1), ("timestamp", -1)])
    await db.sensor_data.create_index("timestamp")
    await db.decisions.create_index([("field_id", 1), ("created_at", -1)])
    await db.decisions.create_index("created_at")
    await db.events.create_index("timestamp")
    print("اتصال به دیتابیس برقرار شد.")


async def close_db():
    global client
    if client:
        client.close()
        print("اتصال به دیتابیس بسته شد.")


def get_db():
    return db
