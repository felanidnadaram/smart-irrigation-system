# راهنمای تست سیستم کشاورزی هوشمند

## Test Strategy

Three types of automated tests:

| Type | What it tests | Files |
|------|--------------|-------|
| **Unit** | Pure business logic (no DB/API) | `test_decisions.py` |
| **Integration** | Service + DB interactions | `test_sensors.py`, `test_system_flows.py` |
| **System/API** | Full HTTP request/response cycle | `test_auth.py`, `test_fields.py`, `test_admin.py` |

## Database Isolation

- Tests use a **separate MongoDB database**: `precision_agriculture_test`
- Configured via `TESTING=1` environment variable in `tests/conftest.py`
- Every test gets a **fresh clean database** (all collections deleted before and after each test)
- The production database (`precision_agriculture`) is **never touched**

## How to Run

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_decisions.py

# Run specific test
pytest tests/test_auth.py::test_admin_login_success
```

**Prerequisites:**
- MongoDB running on `mongodb://localhost:27017`
- Install dependencies: `pip install pytest pytest-cov httpx pytest-asyncio`

## Implemented Test Cases (46 total)

### Authentication (`test_auth.py` - 8 tests)
| # | Test | Description |
|---|------|-------------|
| 1 | `test_admin_login_success` | Admin can login and receives token |
| 2 | `test_farmer_login_success` | Farmer can login and receives token |
| 3 | `test_login_wrong_password_fails` | Wrong password returns 401 with Persian message |
| 4 | `test_login_nonexistent_user_fails` | Non-existent user returns 401 |
| 5 | `test_register_new_user` | New user registration works |
| 6 | `test_register_duplicate_username_fails` | Duplicate username rejected |
| 7 | `test_get_me_returns_current_user` | /auth/me returns correct user info |
| 8 | `test_invalid_token_is_rejected` | Invalid JWT token returns 401 |

### Fields (`test_fields.py` - 8 tests)
| # | Test | Description |
|---|------|-------------|
| 9 | `test_farmer_can_create_field` | Farmer creates a field successfully |
| 10 | `test_farmer_can_list_own_fields` | Farmer sees only own fields |
| 11 | `test_farmer_can_update_own_field` | Farmer updates own field |
| 12 | `test_farmer_cannot_update_other_farmer_field` | Cross-farm update blocked (404) |
| 13 | `test_farmer_can_delete_own_field` | Farmer deletes own field |
| 14 | `test_farmer_cannot_access_other_farmer_field` | Cross-farm access blocked (403) |
| 15 | `test_farmer_cannot_list_fields_without_auth` | Unauthenticated access blocked |
| 16 | `test_farmer_update_empty_body_fails` | Empty update returns 400 |

### Sensors (`test_sensors.py` - 5 tests)
| # | Test | Description |
|---|------|-------------|
| 17 | `test_manual_sensor_generation_creates_reading` | POST /generate creates reading |
| 18 | `test_latest_readings_returns_newest_reading` | GET /latest returns most recent |
| 19 | `test_historical_sensor_query_by_time_range` | History query with time range works |
| 20 | `test_farmer_cannot_generate_for_other_field` | Cross-farm generation blocked |
| 21 | `test_historical_data_generation` | Generate historical data endpoint works |

### Decisions (`test_decisions.py` - 11 tests)
| # | Test | Description |
|---|------|-------------|
| 22 | `test_low_soil_moisture_creates_irrigation_recommendation` | Low moisture triggers irrigation |
| 23 | `test_critical_low_moisture_creates_critical_priority` | Very low moisture = critical priority |
| 24 | `test_high_temperature_creates_alert` | High temp triggers temperature alert |
| 25 | `test_critical_high_temperature` | Extreme temp = critical priority |
| 26 | `test_low_temperature_creates_alert` | Low temp triggers alert |
| 27 | `test_high_humidity_creates_alert` | High humidity triggers alert |
| 28 | `test_low_humidity_creates_alert` | Low humidity triggers alert |
| 29 | `test_high_light_intensity_creates_alert` | High light triggers alert |
| 30 | `test_normal_values_produce_no_decisions` | Normal values = no alerts |
| 31 | `test_custom_thresholds_are_respected` | Custom thresholds change behavior |
| 32 | `test_multiple_alerts_for_worst_case` | Worst case produces 4+ alerts |

### Admin (`test_admin.py` - 8 tests)
| # | Test | Description |
|---|------|-------------|
| 33 | `test_farmer_cannot_access_admin_endpoint` | Farmer blocked from admin API |
| 34 | `test_admin_can_access_stats` | Admin gets system statistics |
| 35 | `test_admin_can_manage_users` | Admin lists all users |
| 36 | `test_admin_can_update_global_thresholds` | Admin updates thresholds |
| 37 | `test_admin_can_list_all_fields` | Admin sees all fields |
| 38 | `test_admin_can_list_decisions` | Admin sees all decisions |
| 39 | `test_admin_can_view_events` | Admin views system events |
| 40 | `test_admin_cannot_delete_own_account` | Admin cannot self-delete |

### System Flows (`test_system_flows.py` - 6 tests)
| # | Test | Description |
|---|------|-------------|
| 41 | `test_create_field_and_generate_sensor_data` | Full flow: create field + generate data |
| 42 | `test_decisions_stored_and_retrievable` | Decisions stored in DB and retrievable |
| 43 | `test_threshold_change_affects_decisions` | Threshold update changes decision output |
| 44 | `test_farmer_field_ownership_integrity` | Field ownership isolation verified |
| 45 | `test_recommendations_endpoint_returns_expected_decisions` | Recommendations have correct structure |
| 46 | `test_admin_generate_all_fields` | Admin bulk generation works |

## Coverage Summary

| Module | Coverage |
|--------|----------|
| `app/routers/auth.py` | 93% |
| `app/routers/fields.py` | 92% |
| `app/routers/sensors.py` | 92% |
| `app/services/sensor_generator.py` | 94% |
| `app/routers/dashboard_admin.py` | 76% |
| `app/services/decisions.py` | 75% |
| `app/main.py` | 81% |
| **Overall** | **67%** |

## File Structure

```
tests/
  __init__.py
  conftest.py          # Fixtures: client, test_db, users, sample_field
  test_auth.py         # 8 authentication tests
  test_fields.py       # 8 field management tests
  test_sensors.py      # 5 sensor data tests
  test_decisions.py    # 11 decision/recommendation unit tests
  test_admin.py        # 8 admin dashboard tests
  test_system_flows.py # 6 end-to-end integration tests
pytest.ini             # pytest configuration
```
