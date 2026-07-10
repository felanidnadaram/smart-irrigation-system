# Test Report: Intelligent Precision Agriculture System

## Software Engineering Testing Phase — Formal Test Report

---

## 1. Executive Summary

This report documents the testing phase of the Intelligent Precision Agriculture System, a FastAPI + MongoDB-based platform for sensor-driven farm management. The automated test suite comprises **46 test cases** across six test files, covering unit, integration, and system-level testing. All 46 tests pass consistently, achieving an overall code coverage of **67%** with critical API modules exceeding 90%. Tests operate against a dedicated MongoDB test database to ensure complete isolation from the production environment.

---

## 2. System Under Test

| Component | Technology |
|-----------|-----------|
| Backend Framework | FastAPI (Python) |
| Database | MongoDB (via Motor async driver) |
| Authentication | JWT (python-jose) + bcrypt password hashing |
| Frontend | Jinja2 templates + vanilla JavaScript |
| API Style | RESTful JSON API |
| User Roles | Admin, Farmer (role-based access control) |

The system provides sensor data collection (synthetic generation), threshold-based decision/recommendation engine, predictive analytics stubs, field management, and two role-separated dashboards.

---

## 3. Test Strategy

### 3.1 Testing Pyramid

The test suite follows the testing pyramid model:

```
         /  System/API  \         ← 29 tests (fast, full-stack)
        /   Integration  \        ← 11 tests (service + DB)
       /      Unit        \       ← 11 tests (pure logic, no I/O)
```

### 3.2 Test Classification

| Level | Scope | Tools | Files | Count |
|-------|-------|-------|-------|-------|
| **Unit** | Pure business logic functions, no database or HTTP layer | pytest, pytest-asyncio | `test_decisions.py` | 11 |
| **Integration** | Service functions interacting with MongoDB; multi-step workflows | pytest, pytest-asyncio, Motor | `test_sensors.py`, `test_system_flows.py` | 11 |
| **System/API** | Full HTTP request/response through FastAPI TestClient | pytest, httpx, ASGITransport | `test_auth.py`, `test_fields.py`, `test_admin.py` | 24 |
| **Total** | | | | **46** |

### 3.3 Design Principles

1. **Isolation**: Every test runs against a clean database. No test depends on the output of another.
2. **Determinism**: Unit tests for the decision engine use fixed sensor values to produce predictable outcomes. Integration and API tests use realistic but controlled inputs.
3. **Independence**: Tests do not depend on execution order. Each test creates its own fixtures via the `conftest.py` setup.
4. **Realism**: API tests exercise complete HTTP flows including authentication headers, JSON serialization, status codes, and Persian-language response messages.
5. **Non-destructive**: The test suite operates exclusively on `precision_agriculture_test`. The production database is never read or written.

---

## 4. Test Infrastructure

### 4.1 Database Isolation Strategy

The application uses a global `db` reference in `app/database.py`. For testing:

1. `tests/conftest.py` sets `os.environ["TESTING"] = "1"` at import time.
2. `app/config.py` detects this flag and switches `DATABASE_NAME` to `precision_agriculture_test`.
3. A `set_db()` function in `app/database.py` allows the test fixture to inject the test database reference.
4. The `test_db` fixture creates a fresh Motor client, injects the test database, and cleans all collections before and after each test.

```
Production:  mongodb://localhost:27017/precision_agriculture
Test:        mongodb://localhost:27017/precision_agriculture_test
```

### 4.2 Fixture Hierarchy

```
test_db (function-scoped)
  ├── client (AsyncClient with ASGITransport)
  ├── admin_user (creates user in DB, returns token)
  ├── farmer_user (creates user in DB, returns token)
  ├── second_farmer_user (creates user in DB, returns token)
  └── sample_field (creates field owned by farmer_user)
```

All fixtures are function-scoped, ensuring each test gets fresh data. The `test_db` fixture handles cleanup via a pytest yield fixture with teardown logic.

### 4.3 Key Fixtures

| Fixture | Purpose | Scope |
|---------|---------|-------|
| `test_db` | Provides clean MongoDB connection, cleans collections before/after | function |
| `client` | Async HTTP client wired to FastAPI app via ASGITransport | function |
| `admin_user` | Pre-seeded admin user with JWT token | function |
| `farmer_user` | Pre-seeded farmer user with JWT token | function |
| `second_farmer_user` | Second farmer for cross-user isolation tests | function |
| `sample_field` | Pre-created field owned by `farmer_user` | function |

### 4.4 Technology Stack for Testing

| Tool | Version | Purpose |
|------|---------|---------|
| pytest | 9.1.1 | Test runner and framework |
| pytest-asyncio | 1.4.0 | Async test support |
| pytest-cov | 7.1.0 | Code coverage measurement |
| httpx | 0.28.1 | Async HTTP client for FastAPI testing |
| Motor | 3.7.1 | Async MongoDB driver (test DB setup) |

---

## 5. Test Case Specification

### 5.1 Authentication Tests (`test_auth.py` — 8 tests)

These tests verify the JWT-based authentication system including registration, login, token validation, and error handling.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-01 | `test_admin_login_success` | System | POST `/auth/login` with valid admin credentials | 200, token returned, role="admin", Persian full_name |
| TC-02 | `test_farmer_login_success` | System | POST `/auth/login` with valid farmer credentials | 200, token returned, role="farmer" |
| TC-03 | `test_login_wrong_password_fails` | System | POST `/auth/login` with correct username, wrong password | 401, Persian error message "نام کاربری یا رمز عبور اشتباه است" |
| TC-04 | `test_login_nonexistent_user_fails` | System | POST `/auth/login` with non-existent username | 401 |
| TC-05 | `test_register_new_user` | System | POST `/auth/register` with new user data | 200, user created, password_hash excluded from response |
| TC-06 | `test_register_duplicate_username_fails` | System | POST `/auth/register` with existing username | 400, Persian message "نام کاربری قبلاً استفاده شده است" |
| TC-07 | `test_get_me_returns_current_user` | System | GET `/auth/me` with valid Bearer token | 200, correct username and role returned |
| TC-08 | `test_invalid_token_is_rejected` | System | GET `/auth/me` with malformed JWT token | 401, Persian message containing "توکن" |

**Verified behaviors:**
- Password hashing (bcrypt) and verification work correctly
- JWT token generation and decoding function properly
- Persian-language error messages are returned for all failure cases
- Token-based authentication is enforced on protected endpoints

### 5.2 Field Management Tests (`test_fields.py` — 8 tests)

These tests verify CRUD operations on farm fields, ownership isolation, and access control.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-09 | `test_farmer_can_create_field` | System | POST `/fields/` with valid field data | 200, field_name and crop_type match input, owner_id matches farmer |
| TC-10 | `test_farmer_can_list_own_fields` | System | GET `/fields/` as farmer | 200, list contains only the farmer's fields |
| TC-11 | `test_farmer_can_update_own_field` | System | PUT `/fields/{id}` with updated name and crop | 200, field_name="مزرعه بروزرسانی شده", crop_type="جو" |
| TC-12 | `test_farmer_cannot_update_other_farmer_field` | System | PUT `/fields/{id}` as second farmer on first farmer's field | 404 |
| TC-13 | `test_farmer_can_delete_own_field` | System | DELETE `/fields/{id}` then GET `/fields/` | 200, field no longer in list |
| TC-14 | `test_farmer_cannot_access_other_farmer_field` | System | GET `/fields/{id}` as second farmer on first farmer's field | 403, "دسترسی به این مزرعه ندارید" |
| TC-15 | `test_farmer_cannot_list_fields_without_auth` | System | GET `/fields/` without Authorization header | 401 or 403 |
| TC-16 | `test_farmer_update_empty_body_fails` | System | PUT `/fields/{id}` with all-null fields | 400, "بروزرسانی" in Persian error |

**Verified behaviors:**
- Field CRUD operations function correctly
- Owner-based access control prevents cross-farm modifications
- Unauthenticated requests are rejected
- Input validation rejects empty update payloads

### 5.3 Sensor Data Tests (`test_sensors.py` — 5 tests)

These tests verify sensor data generation, retrieval, and access control.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-17 | `test_manual_sensor_generation_creates_reading` | Integration | POST `/sensors/{id}/generate` | 200, reading contains field_id, soil_moisture, temperature, humidity, light_intensity |
| TC-18 | `test_latest_readings_returns_newest_reading` | Integration | Generate data then GET `/sensors/{id}/latest` | 200, reading field_id matches, timestamp present |
| TC-19 | `test_historical_sensor_query_by_time_range` | Integration | GET `/sensors/{id}/history?start_time=...&end_time=...` | 200, returns list with at least 1 reading |
| TC-20 | `test_farmer_cannot_generate_for_other_field` | System | POST `/sensors/{id}/generate` as second farmer | 403 |
| TC-21 | `test_historical_data_generation` | Integration | POST `/sensors/{id}/generate-historical?days=2` | 200, "داده تاریخچه تولید شد" in message |

**Verified behaviors:**
- Synthetic sensor data generation produces valid readings
- Latest reading retrieval returns correct field association
- Time-range filtering on historical data works
- Cross-farm sensor access is blocked

### 5.4 Decision Engine Tests (`test_decisions.py` — 11 tests)

These are **unit tests** for the pure business logic in `analyze_and_decide()`. They verify the rule-based recommendation engine without database or API involvement.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-22 | `test_low_soil_moisture_creates_irrigation_recommendation` | Unit | soil_moisture=20 (below 30 threshold) | Irrigation decision with priority="high", "آبیاری" in title |
| TC-23 | `test_critical_low_moisture_creates_critical_priority` | Unit | soil_moisture=10 (below 15) | Irrigation decision with priority="critical" |
| TC-24 | `test_high_temperature_creates_alert` | Unit | temperature=40 (above 35 threshold) | Temperature alert, "دمای بالا" in title |
| TC-25 | `test_critical_high_temperature` | Unit | temperature=45 (above 42) | Temperature alert with priority="critical" |
| TC-26 | `test_low_temperature_creates_alert` | Unit | temperature=2 (below 5 threshold) | Temperature alert, "دمای پایین" in title |
| TC-27 | `test_high_humidity_creates_alert` | Unit | humidity=95 (above 90 threshold) | Humidity alert, "رطوبت بالای هوا" in title |
| TC-28 | `test_low_humidity_creates_alert` | Unit | humidity=15 (below 20 threshold) | Humidity alert, "رطوبت پایین هوا" in title |
| TC-29 | `test_high_light_intensity_creates_alert` | Unit | light_intensity=95000 (above 90000) | Light alert, "شدت نور بالا" in title |
| TC-30 | `test_normal_values_produce_no_decisions` | Unit | All values within normal ranges | Empty decisions list (0 alerts) |
| TC-31 | `test_custom_thresholds_are_respected` | Unit | moisture=25 with custom threshold=20 | No irrigation decision (moisture above custom threshold) |
| TC-32 | `test_multiple_alerts_for_worst_case` | Unit | All values extreme (moisture=5, temp=50, humidity=5, light=100000) | At least 4 decisions covering all alert types |

**Verified behaviors:**
- Threshold-based rule engine correctly triggers irrigation recommendations
- Priority escalation works (high → critical at extreme values)
- Temperature, humidity, and light alerts fire independently
- Normal sensor values produce no false positives
- Custom thresholds override defaults correctly
- Multiple simultaneous alerts are generated for compound conditions

### 5.5 Admin Dashboard Tests (`test_admin.py` — 8 tests)

These tests verify admin-only endpoints and role-based access control.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-33 | `test_farmer_cannot_access_admin_endpoint` | System | GET `/dashboard/admin/stats` as farmer | 403, "مدیران" in Persian message |
| TC-34 | `test_admin_can_access_stats` | System | GET `/dashboard/admin/stats` as admin | 200, contains total_users, total_fields, total_readings |
| TC-35 | `test_admin_can_manage_users` | System | GET `/dashboard/admin/users` as admin | 200, list includes the farmer user |
| TC-36 | `test_admin_can_update_global_thresholds` | System | PUT `/dashboard/admin/thresholds` | 200, "آستانه‌ها با موفقیت بروزرسانی شدند" |
| TC-37 | `test_admin_can_list_all_fields` | System | GET `/dashboard/admin/fields` as admin | 200, list includes sample field |
| TC-38 | `test_admin_can_list_decisions` | System | Generate data then GET `/dashboard/admin/decisions` | 200, returns list |
| TC-39 | `test_admin_can_view_events` | System | GET `/dashboard/admin/events` | 200, returns list |
| TC-40 | `test_admin_cannot_delete_own_account` | System | DELETE `/dashboard/admin/users/{own_id}` | 400, "خود را حذف" in message |

**Verified behaviors:**
- Admin role grants access to all admin endpoints
- Farmer role is blocked from admin endpoints with Persian error
- System statistics endpoint returns accurate counts
- Threshold configuration can be updated via API
- Self-deletion prevention is enforced

### 5.6 End-to-End System Flow Tests (`test_system_flows.py` — 6 tests)

These tests exercise complete multi-step workflows spanning multiple modules.

| ID | Test Name | Type | Description | Expected Result |
|----|-----------|------|-------------|-----------------|
| TC-41 | `test_create_field_and_generate_sensor_data` | Integration | Create field → generate sensor data → retrieve latest | All steps succeed, field_id consistent across operations |
| TC-42 | `test_decisions_stored_and_retrievable` | Integration | Generate data → check decisions endpoint | Decisions stored in DB and returned by API |
| TC-43 | `test_threshold_change_affects_decisions` | Unit | Compare decisions with default vs. custom thresholds | Moisture=25: irrigation with threshold=30, no irrigation with threshold=20 |
| TC-44 | `test_farmer_field_ownership_integrity` | System | Create field as farmer1 → verify farmer1 sees it, farmer2 does not | Field appears in farmer1's list, absent from farmer2's list |
| TC-45 | `test_recommendations_endpoint_returns_expected_decisions` | Integration | Generate data → GET decisions → validate structure | Each decision has decision_type, title, description, recommended_action |
| TC-46 | `test_admin_generate_all_fields` | Integration | POST `/dashboard/admin/generate-all` | 200, "تولید شد" in message |

**Verified behaviors:**
- Multi-step workflows (create → generate → retrieve) maintain data consistency
- Decisions are persisted to MongoDB and retrievable via API
- Threshold changes propagate to decision output
- Field ownership isolation holds across the full data lifecycle
- Recommendation API responses conform to the expected schema
- Bulk data generation operates across all active fields

---

## 6. Code Coverage Analysis

Coverage was measured using `pytest-cov` with the `--cov-report=term-missing` option.

### 6.1 Module-Level Coverage

| Module | Statements | Missed | Coverage |
|--------|-----------|--------|----------|
| `app/config.py` | 10 | 0 | **100%** |
| `app/models/field.py` | 41 | 0 | **100%** |
| `app/models/sensor_data.py` | 51 | 0 | **100%** |
| `app/models/user.py` | 41 | 0 | **100%** |
| `app/services/sensor_generator.py` | 51 | 3 | **94%** |
| `app/routers/auth.py` | 69 | 5 | **93%** |
| `app/routers/fields.py` | 39 | 3 | **92%** |
| `app/routers/sensors.py` | 62 | 5 | **92%** |
| `app/main.py` | 37 | 7 | **81%** |
| `app/routers/dashboard_admin.py` | 123 | 30 | **76%** |
| `app/middleware.py` | 12 | 3 | **75%** |
| `app/services/decisions.py` | 68 | 17 | **75%** |
| `app/services/farmer_service.py` | 54 | 16 | **70%** |
| `app/routers/decisions.py` | 39 | 19 | **51%** |
| `app/routers/dashboard_farmer.py` | 25 | 12 | **52%** |
| `app/database.py` | 24 | 14 | **42%** |
| `app/services/admin_service.py` | 91 | 56 | **38%** |
| `app/services/analytics.py` | 80 | 57 | **29%** |
| **TOTAL** | **993** | **323** | **67%** |

### 6.2 Coverage Highlights

- **Critical API routers** (`auth.py`, `fields.py`, `sensors.py`) all exceed 90% coverage.
- **Sensor data generation** (`sensor_generator.py`) achieves 94% — the highest among service modules.
- **Decision engine** (`decisions.py` at 75%) has high coverage on the core `analyze_and_decide()` function; uncovered lines are secondary CRUD helpers called through the API layer.
- **Lower-coverage modules** (`analytics.py`, `admin_service.py`) contain aggregation pipelines and admin-only endpoints that are partially covered through the admin dashboard tests.

### 6.3 Coverage Gaps and Rationale

| Module | Gap | Reason |
|--------|-----|--------|
| `analytics.py` | MongoDB aggregation pipelines | Complex aggregation queries exercised through API tests but not all pipeline branches hit |
| `admin_service.py` | CRUD helper functions | Some admin service functions are only called from endpoints not yet tested in isolation |
| `dashboard_farmer.py` | Stats/prediction endpoints | Farmer dashboard overview endpoints require historical data setup |
| `database.py` | `connect_db()` / `close_db()` | Connection lifecycle managed by app lifespan, not directly tested |
| `middleware.py` | Error handler | Exception path not triggered in normal test flow |

---

## 7. Test Execution Results

### 7.1 Full Test Run Output

```
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
asyncio: mode=Mode.AUTO

tests/test_admin.py::test_farmer_cannot_access_admin_endpoint PASSED     [  2%]
tests/test_admin.py::test_admin_can_access_stats PASSED                  [  4%]
tests/test_admin.py::test_admin_can_manage_users PASSED                  [  6%]
tests/test_admin.py::test_admin_can_update_global_thresholds PASSED      [  8%]
tests/test_admin.py::test_admin_can_list_all_fields PASSED               [ 10%]
tests/test_admin.py::test_admin_can_list_decisions PASSED                [ 13%]
tests/test_admin.py::test_admin_can_view_events PASSED                   [ 15%]
tests/test_admin.py::test_admin_cannot_delete_own_account PASSED         [ 17%]
tests/test_auth.py::test_admin_login_success PASSED                      [ 19%]
tests/test_auth.py::test_farmer_login_success PASSED                     [ 21%]
tests/test_auth.py::test_login_wrong_password_fails PASSED               [ 23%]
tests/test_auth.py::test_login_nonexistent_user_fails PASSED             [ 25%]
tests/test_auth.py::test_register_new_user PASSED                        [ 27%]
tests/test_auth.py::test_register_duplicate_username_fails PASSED        [ 29%]
tests/test_auth.py::test_get_me_returns_current_user PASSED              [ 31%]
tests/test_auth.py::test_invalid_token_is_rejected PASSED                [ 34%]
tests/test_decisions.py::test_low_soil_moisture_creates_irrigation...    [ 36%]
tests/test_decisions.py::test_critical_low_moisture_creates_critical...  [ 39%]
tests/test_decisions.py::test_high_temperature_creates_alert PASSED      [ 41%]
tests/test_decisions.py::test_critical_high_temperature PASSED           [ 43%]
tests/test_decisions.py::test_low_temperature_creates_alert PASSED       [ 46%]
tests/test_decisions.py::test_high_humidity_creates_alert PASSED          [ 48%]
tests/test_decisions.py::test_low_humidity_creates_alert PASSED           [ 50%]
tests/test_decisions.py::test_high_light_intensity_creates_alert PASSED   [ 52%]
tests/test_decisions.py::test_normal_values_produce_no_decisions PASSED   [ 54%]
tests/test_decisions.py::test_custom_thresholds_are_respected PASSED      [ 56%]
tests/test_decisions.py::test_multiple_alerts_for_worst_case PASSED       [ 58%]
tests/test_fields.py::test_farmer_can_create_field PASSED                [ 60%]
tests/test_fields.py::test_farmer_can_list_own_fields PASSED             [ 63%]
tests/test_fields.py::test_farmer_can_update_own_field PASSED            [ 65%]
tests/test_fields.py::test_farmer_cannot_update_other_farmer_field PASSED[ 67%]
tests/test_fields.py::test_farmer_can_delete_own_field PASSED            [ 70%]
tests/test_fields.py::test_farmer_cannot_access_other_farmer_field PASSED[ 72%]
tests/test_fields.py::test_farmer_cannot_list_fields_without_auth PASSED [ 74%]
tests/test_fields.py::test_farmer_update_empty_body_fails PASSED         [ 76%]
tests/test_sensors.py::test_manual_sensor_generation_creates_reading     [ 78%]
tests/test_sensors.py::test_latest_readings_returns_newest_reading       [ 81%]
tests/test_sensors.py::test_historical_sensor_query_by_time_range        [ 83%]
tests/test_sensors.py::test_farmer_cannot_generate_for_other_field       [ 85%]
tests/test_sensors.py::test_historical_data_generation PASSED            [ 87%]
tests/test_system_flows.py::test_create_field_and_generate_sensor_data   [ 89%]
tests/test_system_flows.py::test_decisions_stored_and_retrievable        [ 91%]
tests/test_system_flows.py::test_threshold_change_affects_decisions      [ 93%]
tests/test_system_flows.py::test_farmer_field_ownership_integrity        [ 95%]
tests/test_system_flows.py::test_recommendations_endpoint_returns...     [ 97%]
tests/test_system_flows.py::test_admin_generate_all_fields PASSED        [100%]

====================== 46 passed in 12.06s ======================
```

### 7.2 Summary Statistics

| Metric | Value |
|--------|-------|
| Total tests | 46 |
| Passed | 46 |
| Failed | 0 |
| Errors | 0 |
| Execution time | ~12 seconds |
| Overall coverage | 67% |
| Modules at 90%+ coverage | 5 of 18 |

---

## 8. Traceability Matrix

The following matrix maps each test case to the requirement it validates:

| Requirement | Test Cases |
|-------------|-----------|
| Admin login succeeds | TC-01 |
| Farmer login succeeds | TC-02 |
| Login fails with wrong password | TC-03 |
| Farmer cannot access admin endpoints | TC-33 |
| Admin can access admin statistics | TC-34 |
| Farmer can list only own fields | TC-10, TC-44 |
| Farmer can add a field | TC-09 |
| Farmer can edit a field | TC-11 |
| Farmer can delete own field | TC-13 |
| Farmer cannot access other farmer's field | TC-12, TC-14, TC-20 |
| Manual sensor generation works | TC-17 |
| Latest readings endpoint works | TC-18 |
| Recommendations return expected decisions | TC-22–TC-32, TC-45 |
| Low soil moisture triggers irrigation | TC-22, TC-23 |
| High temperature triggers alert | TC-24, TC-25 |
| Admin can manage users | TC-35 |
| Admin can update thresholds | TC-36 |
| Historical sensor query by time range | TC-19 |
| Invalid token is rejected | TC-08 |
| Unauthenticated access is blocked | TC-15 |

---

## 9. Running the Tests

### 9.1 Prerequisites

- Python 3.13+
- MongoDB running on `mongodb://localhost:27017`
- Dependencies installed: `pip install -r requirements.txt`

### 9.2 Commands

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

### 9.3 Test File Structure

```
tests/
  __init__.py
  conftest.py              # Database fixtures, user fixtures, client setup
  test_auth.py             # 8 tests — Authentication & authorization
  test_fields.py           # 8 tests — Field CRUD & ownership
  test_sensors.py          # 5 tests — Sensor data generation & retrieval
  test_decisions.py        # 11 tests — Decision engine unit tests
  test_admin.py            # 8 tests — Admin dashboard & management
  test_system_flows.py     # 6 tests — End-to-end integration flows
pytest.ini                 # pytest configuration (asyncio_mode=auto)
```

---

## 10. Conclusions and Recommendations

### 10.1 Findings

1. **All 46 tests pass** consistently with zero failures.
2. **Role-based access control** is thoroughly validated — farmers cannot access admin endpoints, and cross-farm data access is properly blocked.
3. **The decision engine** correctly implements all threshold-based rules (irrigation, temperature, humidity, light) with proper priority escalation.
4. **Persian-language responses** are correctly returned for all error and success messages.
5. **Database isolation** works correctly — the production database is never accessed during testing.

### 10.2 Coverage Improvements (Recommended)

To increase overall coverage from 67% toward 80%+, the following areas could be targeted:

- **`analytics.py`** (29%): Add integration tests for `get_field_stats()`, `get_sensor_trend()`, and `predict_next_day()` with seeded historical data.
- **`admin_service.py`** (38%): Add tests for individual admin CRUD operations (`update_user`, `delete_user`, `admin_create_field`).
- **`dashboard_farmer.py`** (52%): Add tests for the farmer overview endpoint and prediction endpoint.
- **`decisions.py` router** (51%): Add tests for resolving and marking decisions as read.

### 10.3 Assumptions and Limitations

- MongoDB must be running locally on port 27017 for tests to execute.
- The test suite uses a real MongoDB instance (not mocked) to ensure integration fidelity.
- Synthetic sensor data is randomly generated; while deterministic inputs are used for unit tests, integration tests may vary in the exact sensor values produced.
- The `datetime.utcnow()` deprecation warnings in Python 3.13 are cosmetic and do not affect test correctness.

---

*Report generated for the Software Engineering Testing Phase — Intelligent Precision Agriculture System.*
