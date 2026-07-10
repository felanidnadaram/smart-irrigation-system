# Intelligent Precision Agriculture System

A sensor-driven farm management platform that generates environmental readings, evaluates conditions against configurable thresholds, and produces automated irrigation recommendations and environmental alerts. Built as a Software Engineering course project.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Seeding Sample Data](#seeding-sample-data)
- [API Reference](#api-reference)
- [Frontend Dashboards](#frontend-dashboards)
- [Testing](#testing)
- [Default Credentials](#default-credentials)

---

## Project Overview

Agriculture depends on timely responses to changing environmental conditions. This system simulates an IoT sensor network deployed across farm fields, continuously collecting data on soil moisture, temperature, humidity, and light intensity. A rule-based decision engine evaluates each reading against configurable thresholds and generates recommendations such as "irrigate field X today" or "high temperature alert."

Two user roles interact with the system:

- **Farmer** — manages owned fields, views sensor data and trends, receives recommendations.
- **Administrator** — manages all users and fields, monitors system-wide statistics, configures decision thresholds.

The system stores all data in MongoDB and exposes both a REST API and server-rendered dashboards.

---

## Key Features

### Authentication and Authorization

- User registration with role assignment (`farmer` or `admin`).
- JWT-based login with configurable token expiration (default: 24 hours).
- Current-user retrieval via `GET /auth/me`.
- Password hashing with bcrypt.
- Role-based endpoint protection using FastAPI dependency injection.
- Farmer and admin role guards (`require_farmer`, `require_admin`).

### Field Management

- CRUD operations on agricultural fields (create, read, update, delete).
- Each field has: name, location, crop type, area (hectares), notes, and irrigation schedule.
- Ownership enforcement — farmers can only access and modify their own fields.
- Isolation between farmers — cross-farm access returns `403 Forbidden` or `404 Not Found`.
- Admin can manage all fields across all farmers.

### Sensor Data Management

- Synthetic sensor data generation with realistic diurnal patterns (temperature peaks at midday, light intensity follows sun arc).
- Supported measurements: soil moisture, temperature, humidity, light intensity, soil pH, wind speed, rainfall.
- Latest reading retrieval per field.
- Historical data query with optional time-range filtering (`start_time`, `end_time`) and configurable limit.
- On-demand single reading generation (`POST /sensors/{id}/generate`).
- Bulk historical data generation for a configurable number of days (`POST /sensors/{id}/generate-historical`).
- Automatic 7-day historical data generation when a new field is created.

### Decision and Recommendation Engine

- Rule-based evaluation of sensor readings against configurable thresholds.
- Decision types produced:

  | Type | Trigger |
  |------|---------|
  | `irrigation` | Soil moisture below minimum or above maximum |
  | `temperature_alert` | Temperature above maximum or below minimum |
  | `humidity_alert` | Humidity below minimum or above maximum |
  | `light_alert` | Light intensity above maximum |

- Priority levels: `low`, `medium`, `high`, `critical` — severity escalates at extreme values.
- Multiple simultaneous alerts for compound worst-case conditions.
- Decisions stored in MongoDB with `is_read` and `is_resolved` status flags.
- Farmers can resolve or mark decisions as read.
- Global thresholds configurable by administrators via API.

### Administration

- View all users, update user properties (name, phone, role, active status), delete users.
- Self-deletion prevention — administrators cannot delete their own account.
- Cascade deletion — deleting a user removes their fields.
- View and manage all fields across the system.
- View all decisions system-wide.
- Configure global decision thresholds (`soil_moisture_low`, `temperature_high`, etc.).
- System-wide statistics: total users, fields, readings, decisions, 24-hour averages.
- System event log tracking (startup, seed, operational events).
- Bulk sensor data generation for all active fields.

---

## System Architecture

### Layered Structure

```text
Client Request
      |
      v
FastAPI Router Layer (app/routers/)
      |
      v
Authentication Dependencies (app/routers/auth.py)
      |
      v
Pydantic Validation Schemas (app/models/)
      |
      v
Business Logic Services (app/services/)
      |
      v
MongoDB via Motor Async Driver (app/database.py)
      |
      v
JSON Response
```

### Layer Responsibilities

| Layer | Directory | Responsibility |
|-------|-----------|---------------|
| **Entry Point** | `app/main.py` | FastAPI app creation, lifespan management, middleware registration, router inclusion, static file and template mounting |
| **Configuration** | `app/config.py` | Environment variables, database name, JWT settings, default decision thresholds |
| **Database** | `app/database.py` | Motor client lifecycle, database connection, index creation, global `db` accessor |
| **Routers** | `app/routers/` | HTTP endpoint definitions, request validation, response formatting |
| **Authentication** | `app/routers/auth.py` | JWT creation/verification, password hashing, role-based dependency functions |
| **Models** | `app/models/` | Pydantic schemas for request validation and response serialization |
| **Services** | `app/services/` | Business logic — sensor generation, decision analysis, analytics, CRUD operations |
| **Middleware** | `app/middleware.py` | Global exception handling with Persian error messages |
| **Utilities** | `app/utils/` | Persian message constants and helper functions |
| **Templates** | `app/templates/` | Jinja2 HTML templates for login, farmer dashboard, admin dashboard |
| **Static Assets** | `app/static/` | CSS stylesheets and JavaScript clients for both dashboards |
| **Tests** | `tests/` | Unit, integration, and system-level automated tests |

### Database Collections

| Collection | Purpose | Key Indexes |
|------------|---------|-------------|
| `users` | User accounts | `username` (unique), `role` |
| `fields` | Farm field records | `owner_id` |
| `sensor_data` | Sensor readings | `(field_id, timestamp)`, `timestamp` |
| `decisions` | Recommendations and alerts | `(field_id, created_at)`, `created_at` |
| `events` | System event log | `timestamp` |
| `settings` | Global configuration (thresholds) | `_id` |

---

## Repository Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment-based configuration
│   ├── database.py              # MongoDB connection and accessor
│   ├── middleware.py             # Global error handling middleware
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User, Token, LoginRequest schemas
│   │   ├── field.py             # Field CRUD and response schemas
│   │   ├── sensor_data.py       # Sensor reading schemas
│   │   └── decision.py          # Decision, Threshold, Prediction schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              # /auth — register, login, me
│   │   ├── fields.py            # /fields — farmer field CRUD
│   │   ├── sensors.py           # /sensors — data generation and retrieval
│   │   ├── decisions.py         # /decisions — decision retrieval and resolution
│   │   ├── dashboard_farmer.py  # /dashboard/farmer — farmer overview, stats, predictions
│   │   └── dashboard_admin.py   # /dashboard/admin — admin management and monitoring
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sensor_generator.py  # Synthetic sensor reading generation
│   │   ├── decisions.py         # Rule-based decision engine
│   │   ├── analytics.py         # Aggregation queries, trends, predictions
│   │   ├── farmer_service.py    # Farmer-scoped field operations
│   │   └── admin_service.py     # Admin-scoped operations, event logging
│   ├── templates/
│   │   ├── index.html           # Login page
│   │   ├── farmer_dashboard.html
│   │   └── admin_dashboard.html
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── farmer.js
│   │       └── admin.js
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Persian message constants and helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures, database isolation, client setup
│   ├── test_auth.py             # 8 authentication tests
│   ├── test_fields.py           # 8 field management tests
│   ├── test_sensors.py          # 5 sensor data tests
│   ├── test_decisions.py        # 11 decision engine unit tests
│   ├── test_admin.py            # 8 admin dashboard tests
│   └── test_system_flows.py     # 6 end-to-end integration tests
├── requirements.txt             # Python dependencies
├── pytest.ini                   # pytest configuration
├── run.py                       # Application launcher script
├── seed.py                      # Database seeder with sample data
├── TESTING.md                   # Test suite documentation (Persian)
└── TEST_REPORT.md               # Formal test report (English)
```

---

## Prerequisites

- **Python** 3.10 or later
- **MongoDB** running on `mongodb://localhost:27017`
- **pip** for package installation

---

## Installation

1. Clone or download the repository:

```bash
cd intelligent-precision-agriculture
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

This installs all runtime and testing dependencies:

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `motor` | Async MongoDB driver |
| `pymongo` | MongoDB driver (motor dependency) |
| `pydantic` | Data validation and settings |
| `python-jose[cryptography]` | JWT token creation and verification |
| `bcrypt` | Password hashing |
| `python-multipart` | Form data parsing for FastAPI |
| `jinja2` | Template rendering |
| `pytest` | Test framework |
| `pytest-cov` | Coverage reporting |
| `httpx` | Async HTTP client for API testing |

---

## Configuration

All configuration is handled through environment variables with sensible defaults defined in `app/config.py`.

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `precision_agriculture` | Production database name |
| `TESTING` | `0` | Set to `1` to use test database |
| `TEST_DATABASE_NAME` | `precision_agriculture_test` | Test database name (used when `TESTING=1`) |
| `SECRET_KEY` | `a3f5b8c1d4e7f0a2b6c9d3e8f1a4b7c0d5e9f2a6` | JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Token lifetime |

Default decision thresholds (defined in `app/config.py`):

| Threshold | Default Value | Unit |
|-----------|--------------|------|
| `soil_moisture_low` | 30.0 | % |
| `soil_moisture_high` | 80.0 | % |
| `temperature_high` | 35.0 | °C |
| `temperature_low` | 5.0 | °C |
| `humidity_low` | 20.0 | % |
| `humidity_high` | 90.0 | % |
| `light_intensity_high` | 90000 | lux |

No `.env` file is included in the repository. Set environment variables before starting the application if you need non-default values.

---

## Running the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided launcher script:

```bash
python run.py
```

The application will be available at:

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Login page (root) |
| `http://localhost:8000/dashboard/farmer` | Farmer dashboard |
| `http://localhost:8000/dashboard/admin` | Admin dashboard |
| `http://localhost:8000/docs` | Swagger UI (auto-generated API docs) |
| `http://localhost:8000/redoc` | ReDoc (alternative API docs) |

---

## Seeding Sample Data

The seed script creates sample users, fields, sensor readings, and decisions in the production database.

```bash
python seed.py
```

**Warning:** This drops all existing data in the `users`, `fields`, `sensor_data`, `decisions`, and `events` collections before inserting sample data.

The seed script creates:

| Record | Value |
|--------|-------|
| Admin user | `admin` / `admin123` |
| Farmer user | `farmer1` / `farmer123` |
| Farmer user | `farmer2` / `farmer123` |
| Fields | 3 fields (wheat, pistachio, rice) with 7 days of sensor data each |
| Decisions | Generated from the latest reading of each field |

---

## API Reference

All API endpoints require a `Bearer` token in the `Authorization` header unless noted otherwise. Error messages are returned in Persian (Farsi).

### Authentication — `/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Register a new user |
| `POST` | `/auth/login` | No | Login and receive JWT token |
| `GET` | `/auth/me` | Yes | Get current user information |

**POST /auth/register** — Request body:

```json
{
  "username": "string (3-50 chars)",
  "password": "string (6+ chars)",
  "full_name": "string (2-100 chars)",
  "role": "farmer | admin",
  "phone": "string (optional)"
}
```

**POST /auth/login** — Request body:

```json
{
  "username": "string",
  "password": "string"
}
```

Response:

```json
{
  "access_token": "jwt_token_string",
  "token_type": "bearer",
  "role": "farmer",
  "user_id": "mongodb_object_id",
  "full_name": "user_full_name"
}
```

### Field Management — `/fields`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/fields/` | Farmer | List fields owned by current user |
| `POST` | `/fields/` | Farmer | Create a new field |
| `GET` | `/fields/{field_id}` | Farmer | Get a specific field |
| `PUT` | `/fields/{field_id}` | Farmer | Update a field (owner only) |
| `DELETE` | `/fields/{field_id}` | Farmer | Delete a field (owner only) |

Creating a field automatically generates 7 days of historical sensor data for that field.

### Sensor Data — `/sensors`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/sensors/{field_id}/latest` | Farmer | Get most recent reading |
| `GET` | `/sensors/{field_id}/history` | Farmer | Query readings by time range |
| `POST` | `/sensors/{field_id}/generate` | Farmer | Generate a new reading |
| `POST` | `/sensors/{field_id}/generate-historical` | Farmer | Generate historical readings |

**GET /sensors/{field_id}/history** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_time` | datetime | — | Filter readings after this time |
| `end_time` | datetime | — | Filter readings before this time |
| `limit` | int | 100 | Maximum readings to return (1-1000) |

**POST /sensors/{field_id}/generate-historical** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | int | 7 | Number of days to generate (1-30) |

### Decisions — `/decisions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/decisions/{field_id}` | Farmer | Get decisions for a specific field |
| `GET` | `/decisions/alerts/all` | Farmer | Get all unresolved alerts |
| `PUT` | `/decisions/{decision_id}/resolve` | Farmer | Mark a decision as resolved |
| `PUT` | `/decisions/{decision_id}/read` | Farmer | Mark a decision as read |

### Farmer Dashboard — `/dashboard/farmer`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard/farmer/overview` | Farmer | Dashboard overview with fields, alerts, latest readings |
| `GET` | `/dashboard/farmer/field/{field_id}/stats` | Farmer | Sensor statistics (avg, min, max) over N hours |
| `GET` | `/dashboard/farmer/field/{field_id}/prediction` | Farmer | Next-day prediction using linear extrapolation |
| `GET` | `/dashboard/farmer/field/{field_id}/trend` | Farmer | Time-series trend data for a specific metric |

**GET /dashboard/farmer/field/{field_id}/trend** — Query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `soil_moisture` | Metric to trend: `soil_moisture`, `temperature`, `humidity`, `light_intensity` |
| `hours` | int | 24 | Time window in hours |

### Admin Dashboard — `/dashboard/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/dashboard/admin/stats` | Admin | System-wide statistics |
| `GET` | `/dashboard/admin/users` | Admin | List all users |
| `PUT` | `/dashboard/admin/users/{user_id}` | Admin | Update a user |
| `DELETE` | `/dashboard/admin/users/{user_id}` | Admin | Delete a user |
| `GET` | `/dashboard/admin/fields` | Admin | List all fields |
| `POST` | `/dashboard/admin/fields` | Admin | Create a field for any farmer |
| `PUT` | `/dashboard/admin/fields/{field_id}` | Admin | Update any field |
| `DELETE` | `/dashboard/admin/fields/{field_id}` | Admin | Delete any field |
| `GET` | `/dashboard/admin/decisions` | Admin | List all decisions |
| `GET` | `/dashboard/admin/events` | Admin | View system event log |
| `GET` | `/dashboard/admin/thresholds` | Admin | Get current global thresholds |
| `PUT` | `/dashboard/admin/thresholds` | Admin | Update global thresholds |
| `POST` | `/dashboard/admin/generate-all` | Admin | Generate sensor data for all active fields |

---

## Frontend Dashboards

The application includes server-rendered HTML dashboards:

- **Login Page** (`/`) — Farmer/admin login with role selection tabs. Persian UI.
- **Farmer Dashboard** (`/dashboard/farmer`) — Field list with sensor status, alerts, field management (add/edit/delete), detailed sensor view with stats and predictions.
- **Admin Dashboard** (`/dashboard/admin`) — Tabbed interface for system overview, user management, field management, decision monitoring, and threshold configuration.

Dashboards communicate with the backend via `fetch()` calls to the API endpoints described above. All user-facing text is in Persian (Farsi).

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Verbose output
pytest -v

# With coverage report (terminal)
pytest --cov=app --cov-report=term-missing

# With HTML coverage report
pytest --cov=app --cov-report=html

# Run a specific test file
pytest tests/test_decisions.py

# Run a specific test case
pytest tests/test_auth.py::test_admin_login_success -v
```

### Test Database Isolation

Tests operate on a separate MongoDB database (`precision_agriculture_test`) to ensure the production database is never modified. This is achieved by:

1. `tests/conftest.py` sets `os.environ["TESTING"] = "1"` at import time.
2. `app/config.py` detects this and switches `DATABASE_NAME` to `precision_agriculture_test`.
3. Each test receives a `test_db` fixture that cleans all collections before and after execution.

### Test Inventory

| File | Level | Count | Description |
|------|-------|-------|-------------|
| `test_auth.py` | System | 8 | Login, registration, token validation, error handling |
| `test_fields.py` | System | 8 | CRUD, ownership enforcement, access control |
| `test_sensors.py` | Integration | 5 | Data generation, retrieval, time-range queries |
| `test_decisions.py` | Unit | 11 | Threshold rules, priorities, edge cases |
| `test_admin.py` | System | 8 | Admin endpoints, role guards, self-deletion prevention |
| `test_system_flows.py` | Integration | 6 | End-to-end workflows across multiple modules |
| **Total** | | **46** | |

### Coverage Summary

Overall coverage: **67%**

| Module | Coverage |
|--------|----------|
| `app/services/sensor_generator.py` | 94% |
| `app/routers/auth.py` | 93% |
| `app/routers/fields.py` | 92% |
| `app/routers/sensors.py` | 92% |
| `app/main.py` | 81% |
| `app/routers/dashboard_admin.py` | 76% |
| `app/services/decisions.py` | 75% |
| `app/middleware.py` | 75% |
| `app/services/farmer_service.py` | 70% |
| `app/routers/dashboard_farmer.py` | 52% |
| `app/routers/decisions.py` | 51% |
| `app/database.py` | 42% |
| `app/services/admin_service.py` | 38% |
| `app/services/analytics.py` | 29% |

Detailed test reports are available in [TEST_REPORT.md](TEST_REPORT.md).

---

## Default Credentials

After running `python seed.py`:

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin123` |
| Farmer | `farmer1` | `farmer123` |
| Farmer | `farmer2` | `farmer123` |

These credentials are for development and testing purposes only.
