import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "precision_agriculture")

TESTING = os.getenv("TESTING", "0") == "1"
if TESTING:
    DATABASE_NAME = os.getenv("TEST_DATABASE_NAME", "precision_agriculture_test")

SECRET_KEY = os.getenv("SECRET_KEY", "a3f5b8c1d4e7f0a2b6c9d3e8f1a4b7c0d5e9f2a6")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

THRESHOLDS = {
    "soil_moisture_low": 30.0,
    "soil_moisture_high": 80.0,
    "temperature_high": 35.0,
    "temperature_low": 5.0,
    "humidity_low": 20.0,
    "humidity_high": 90.0,
    "light_intensity_high": 90000,
}
