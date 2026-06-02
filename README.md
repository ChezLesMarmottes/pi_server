# PI Server

PI Server is a lightweight FastAPI-based REST API for managing **devices**, **measurements**, and **automation rules**. It's designed to run on a Raspberry Pi or any local Python environment with minimal resource requirements.

## Overview

PI Server provides a complete automation system with these core capabilities:

- 🔧 **Device Management**: Create and manage devices with state tracking (ON/OFF)
- 📊 **Measurements**: Ingest sensor data (temperature, humidity, pressure, etc.) with structured storage
- ⚙️ **Rules Engine**: Define conditional automation rules that trigger device actions based on measurement thresholds
- 🏥 **Health Monitoring**: Built-in health check endpoint for monitoring and orchestration
- 🧪 **Comprehensive Testing**: Full test suite with 31+ tests covering all endpoints and edge cases

## Features

- **RESTful API** with consistent JSON responses wrapped in an `ApiResponse` envelope
- **Request Validation** using Pydantic v2 with custom validators
- **Automatic Schema Initialization** - SQLite database tables created on startup
- **Real-time Automation** - Rules evaluate immediately when new measurements arrive
- **Retroactive Rule Evaluation** - Rules can be evaluated against historical measurements
- **Case-Insensitive State Management** - Device states and enums accept flexible input
- **Comprehensive Logging** - All operations logged for debugging and monitoring
- **Production-Ready Tests** - 31 tests with proper fixtures and dependency injection
- **Type-Safe Code** - Full type hints with zero type errors (verified with mypy)

## Tech Stack

- **Python** 3.13
- **FastAPI** 0.136.1 - Modern async web framework
- **Pydantic** 2.13.4 - Data validation and serialization
- **SQLite** - Lightweight file-based database
- **Uvicorn** 0.47.0 - ASGI application server
- **Pytest** 9.0.3 - Testing framework with async support
- **mypy** 2.1.0 - Static type checker

## Quick Start

### Prerequisites

- Python 3.11+
- pip or pipenv

### Installation

1. **Clone and navigate to the project**
   ```bash
   cd pi_server
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`

   - Interactive API docs: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_devices.py

# Run with coverage report
pytest --cov=app
```

All 31 tests should pass with no errors.

### Type Checking

```bash
# Check types with mypy
mypy app/
```

## Project Structure

```
pi_server/
├── app/
│   ├── main.py                 # FastAPI app initialization and lifecycle
│   ├── schemas.py              # Pydantic models and data validation
│   ├── class_database.py       # Database abstraction layer
│   ├── crud_helpers.py         # Common CRUD operations
│   ├── get_db.py               # Dependency injection for database
│   ├── rule_engine.py          # Rule evaluation and automation logic
│   └── routes/
│       ├── devices.py          # Device endpoints
│       ├── measurements.py     # Measurement endpoints
│       ├── rules.py            # Rule endpoints
│       └── health.py           # Health check endpoint
├── tests/
│   ├── conftest.py            # Pytest configuration and fixtures
│   ├── test_devices.py        # Device endpoint tests
│   ├── test_measurements.py   # Measurement endpoint tests
│   ├── test_rules.py          # Rule endpoint tests
│   └── test_health.py         # Health endpoint tests
├── data/
│   └── platform.db            # SQLite database (created automatically)
├── requirements.txt           # Python dependencies
├── LICENSE                    # Project license
└── README.md                  # This file
```

## Database Schema

The API stores all data in SQLite at `data/platform.db`. The database is automatically initialized on first startup.

### `devices` Table

Stores device state information.

| Column    | Type    | Constraints                    | Purpose                           |
|-----------|---------|--------------------------------|-----------------------------------|
| id        | INTEGER | PRIMARY KEY, AUTOINCREMENT     | Unique device identifier          |
| name      | TEXT    | UNIQUE NOT NULL                | Unique device name (e.g., "pump") |
| state     | TEXT    | NOT NULL                       | Device state ("ON" or "OFF")      |
| timestamp | TEXT    | NOT NULL                       | UTC ISO-8601 creation/update time |

**Example:**
```
id=1, name="pump", state="OFF", timestamp="2024-06-02T10:30:00+00:00"
```

### `measurements` Table

Stores sensor readings and measurement data.

| Column    | Type    | Constraints               | Purpose                                     |
|-----------|---------|---------------------------|---------------------------------------------|
| id        | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique measurement identifier               |
| source    | TEXT    | NOT NULL                  | Sensor/source identifier (e.g., "sensor-1") |
| name      | TEXT    | NOT NULL                  | Measurement type (e.g., "temperature")      |
| value     | REAL    | NOT NULL                  | Numeric measurement value                   |
| unit      | TEXT    | (optional)                | Unit of measurement (e.g., "°C")            |
| timestamp | TEXT    | NOT NULL                  | UTC ISO-8601 measurement time               |

**Example:**
```
id=42, source="sensor-1", name="temperature", value=22.5, unit="C", timestamp="2024-06-02T10:35:15+00:00"
```

### `rules` Table

Stores automation rules that trigger device actions.

| Column                | Type    | Constraints               | Purpose                                          |
|-----------------------|---------|---------------------------|--------------------------------------------------|
| id                    | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique rule identifier                           |
| name                  | TEXT    | UNIQUE NOT NULL           | Unique rule name                                 |
| enabled               | BOOLEAN | NOT NULL                  | Whether rule is active                           |
| condition_type        | TEXT    | NOT NULL                  | Type of condition ("measurement_threshold")      |
| condition_measurement | TEXT    | NOT NULL                  | Measurement name to watch (e.g., "temperature")  |
| condition_operator    | TEXT    | NOT NULL                  | Comparison operator (">", "<", ">=", "<=", "==") |
| condition_value       | REAL    | NOT NULL                  | Threshold value                                  |
| action_type           | TEXT    | NOT NULL                  | Type of action ("set_device_state")              |
| action_device         | TEXT    | NOT NULL                  | Target device name                               |
| action_state          | TEXT    | NOT NULL                  | Target device state ("ON" or "OFF")              |
| timestamp             | TEXT    | NOT NULL                  | UTC ISO-8601 creation time                       |

**Example:**
```
id=1, name="fan_control", enabled=true, condition_type="measurement_threshold",
condition_measurement="temperature", condition_operator=">", condition_value=25,
action_type="set_device_state", action_device="fan", action_state="ON",
timestamp="2024-06-02T10:00:00+00:00"
```

## API Reference

All endpoints return JSON responses. Most endpoints wrap data in an `ApiResponse` envelope with `status`, `message`, and `data` fields.

### Response Format

**Success Response (2xx):**
```json
{
  "status": "ok",
  "message": "device created",
  "data": {
    "id": 42,
    "name": "pump",
    "state": "OFF",
    "timestamp": "2024-06-02T10:30:00+00:00"
  }
}
```

**Error Response (4xx):**
```json
{
  "status": "error",
  "message": "Device already exists",
  "data": null
}
```

---

## Health Endpoint

### `GET /health`

Check API server health.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

## Device Endpoints

### `POST /devices`

Create a new device.

**Request Body:**
```json
{
  "name": "pump",
  "state": "OFF"
}
```

**Parameters:**
- `name` (string, required): Unique device name (min 1 character)
- `state` (string, required): Device state - "ON" or "OFF" (case-insensitive)

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "device created",
  "data": {
    "id": 1
  }
}
```

**Errors:**
- `400` - Device with this name already exists
- `422` - Invalid request (missing fields, invalid state)

**Example:**
```bash
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "pump", "state": "off"}'
```

---

### `GET /devices`

List all devices with optional filtering and pagination.

**Query Parameters:**
- `name` (string, optional): Filter by device name (exact match)
- `limit` (integer, optional, default=20): Maximum results (1-99)

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got devices",
  "data": [
    {
      "id": 1,
      "name": "pump",
      "state": "OFF",
      "timestamp": "2024-06-02T10:30:00+00:00"
    },
    {
      "id": 2,
      "name": "fan",
      "state": "ON",
      "timestamp": "2024-06-02T10:31:00+00:00"
    }
  ]
}
```

**Examples:**
```bash
# Get all devices
curl http://localhost:8000/devices

# Filter by name
curl http://localhost:8000/devices?name=pump

# Limit results
curl http://localhost:8000/devices?limit=5
```

---

### `GET /devices/{name}`

Get a specific device by name.

**Path Parameters:**
- `name` (string): Device name

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got device pump",
  "data": {
    "id": 1,
    "name": "pump",
    "state": "OFF",
    "timestamp": "2024-06-02T10:30:00+00:00"
  }
}
```

**Errors:**
- `404` - Device not found

**Example:**
```bash
curl http://localhost:8000/devices/pump
```

---

### `POST /devices/{name}/state`

Update a device's state.

**Path Parameters:**
- `name` (string): Device name

**Request Body:**
```json
{
  "state": "ON"
}
```

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "state updated",
  "data": {
    "id": 1,
    "name": "pump",
    "state": "ON",
    "timestamp": "2024-06-02T10:35:00+00:00"
  }
}
```

**Errors:**
- `404` - Device not found
- `422` - Invalid state value

**Example:**
```bash
curl -X POST http://localhost:8000/devices/pump/state \
  -H "Content-Type: application/json" \
  -d '{"state": "on"}'
```

---

## Measurement Endpoints

### `POST /measurements`

Store a new measurement.

**Request Body:**
```json
{
  "source": "sensor-1",
  "name": "temperature",
  "value": 22.5,
  "unit": "C"
}
```

**Parameters:**
- `source` (string, required): Sensor/source identifier (min 1 character)
- `name` (string, required): Measurement type (min 1 character)
- `value` (number, required): Numeric value (must be finite, not NaN or infinity)
- `unit` (string, optional): Unit of measurement

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "measurement stored",
  "data": {
    "id": 42
  }
}
```

**Side Effects:** If enabled rules match this measurement, their actions are executed immediately (real-time automation).

**Errors:**
- `422` - Invalid request (missing fields, non-numeric value, non-finite value)

**Example:**
```bash
curl -X POST http://localhost:8000/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sensor-1",
    "name": "temperature",
    "value": 22.5,
    "unit": "C"
  }'
```

---

### `GET /measurements`

List measurements with optional filtering and pagination.

**Query Parameters:**
- `name` (string, optional): Filter by measurement name (exact match)
- `limit` (integer, optional, default=20): Maximum results (1-99)

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got measurements",
  "data": [
    {
      "id": 42,
      "source": "sensor-1",
      "name": "temperature",
      "value": 22.5,
      "unit": "C",
      "timestamp": "2024-06-02T10:35:15+00:00"
    }
  ]
}
```

**Examples:**
```bash
# Get recent measurements
curl http://localhost:8000/measurements

# Filter by name
curl http://localhost:8000/measurements?name=temperature

# Limit results
curl http://localhost:8000/measurements?limit=10
```

---

### `GET /measurements/latest`

Get the latest measurement for each measurement name.

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got latest measurements",
  "data": [
    {
      "id": 99,
      "source": "sensor-1",
      "name": "temperature",
      "value": 23.8,
      "unit": "C",
      "timestamp": "2024-06-02T10:40:00+00:00"
    },
    {
      "id": 100,
      "source": "sensor-2",
      "name": "humidity",
      "value": 65.2,
      "unit": "%",
      "timestamp": "2024-06-02T10:40:05+00:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/measurements/latest
```

---

## Rule Endpoints

### `POST /rules`

Create a new automation rule.

**Request Body:**
```json
{
  "name": "fan_control",
  "enabled": true,
  "condition_type": "measurement_threshold",
  "condition_measurement": "temperature",
  "condition_operator": ">",
  "condition_value": 25,
  "action_type": "set_device_state",
  "action_device": "fan",
  "action_state": "ON"
}
```

**Parameters:**
- `name` (string, required): Unique rule name (min 1 character)
- `enabled` (boolean, required): Whether rule is active
- `condition_type` (string, required): Currently only "measurement_threshold" supported
- `condition_measurement` (string, required): Name of measurement to monitor (min 1 character)
- `condition_operator` (string, required): Comparison operator: ">", "<", ">=", "<=", "=="
- `condition_value` (number, required): Threshold value to compare against
- `action_type` (string, required): Currently only "set_device_state" supported
- `action_device` (string, required): Target device name (min 1 character)
- `action_state` (string, required): Target device state - "ON" or "OFF"

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "rule created",
  "data": {
    "id": 1
  }
}
```

**Side Effects:** If created with `enabled=true`, the rule is immediately evaluated against all historical measurements and triggered actions are executed (retroactive automation).

**Errors:**
- `400` - Rule with this name already exists
- `422` - Invalid request (missing fields, invalid enum values)

**How Rules Work:**
1. When a new measurement arrives, all enabled rules are evaluated
2. If a rule's condition is met, the action is executed immediately
3. Multiple rules can trigger from a single measurement
4. Retroactive evaluation occurs when a rule is created or re-enabled

**Example:**
```bash
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fan_control",
    "enabled": true,
    "condition_type": "measurement_threshold",
    "condition_measurement": "temperature",
    "condition_operator": ">",
    "condition_value": 25,
    "action_type": "set_device_state",
    "action_device": "fan",
    "action_state": "ON"
  }'
```

---

### `GET /rules`

List all rules with optional filtering and pagination.

**Query Parameters:**
- `name` (string, optional): Filter by rule name (exact match)
- `limit` (integer, optional, default=20): Maximum results (1-99)

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got rules",
  "data": [
    {
      "id": 1,
      "name": "fan_control",
      "enabled": true,
      "condition_type": "measurement_threshold",
      "condition_measurement": "temperature",
      "condition_operator": ">",
      "condition_value": 25,
      "action_type": "set_device_state",
      "action_device": "fan",
      "action_state": "ON",
      "timestamp": "2024-06-02T10:00:00+00:00"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/rules
```

---

### `GET /rules/{name}`

Get a specific rule by name.

**Path Parameters:**
- `name` (string): Rule name

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "got rule fan_control",
  "data": {
    "id": 1,
    "name": "fan_control",
    "enabled": true,
    "condition_type": "measurement_threshold",
    "condition_measurement": "temperature",
    "condition_operator": ">",
    "condition_value": 25,
    "action_type": "set_device_state",
    "action_device": "fan",
    "action_state": "ON",
    "timestamp": "2024-06-02T10:00:00+00:00"
  }
}
```

**Errors:**
- `404` - Rule not found

**Example:**
```bash
curl http://localhost:8000/rules/fan_control
```

---

### `POST /rules/{name}/toggle`

Enable or disable a rule.

**Path Parameters:**
- `name` (string): Rule name

**Request Body:**
```json
{
  "enabled": false
}
```

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "toggle updated",
  "data": {
    "id": 1,
    "name": "fan_control",
    "enabled": false,
    ...
  }
}
```

**Side Effects:** When enabling a rule, it's immediately evaluated against all historical measurements.

**Errors:**
- `404` - Rule not found

**Example:**
```bash
curl -X POST http://localhost:8000/rules/fan_control/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

### `DELETE /rules/{name}`

Delete a rule.

**Path Parameters:**
- `name` (string): Rule name

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "rule fan_control deleted",
  "data": null
}
```

**Errors:**
- `404` - Rule not found

**Example:**
```bash
curl -X DELETE http://localhost:8000/rules/fan_control
```

---

## Usage Examples

### Complete Workflow Example

```bash
# 1. Create devices
curl -X POST http://localhost:8000/devices \
  -H "Content-Type: application/json" \
  -d '{"name": "fan", "state": "off"}'

# 2. Create a rule (fan turns on if temperature > 25°C)
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fan_control",
    "enabled": true,
    "condition_type": "measurement_threshold",
    "condition_measurement": "temperature",
    "condition_operator": ">",
    "condition_value": 25,
    "action_type": "set_device_state",
    "action_device": "fan",
    "action_state": "ON"
  }'

# 3. Submit a temperature measurement (triggers rule)
curl -X POST http://localhost:8000/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sensor-1",
    "name": "temperature",
    "value": 26.5,
    "unit": "C"
  }'

# 4. Check device state (should be ON now)
curl http://localhost:8000/devices/fan

# 5. Get latest measurements
curl http://localhost:8000/measurements/latest

# 6. Disable rule
curl -X POST http://localhost:8000/rules/fan_control/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# 7. Delete rule
curl -X DELETE http://localhost:8000/rules/fan_control
```

---

## Architecture Overview

### Layered Design

The project follows a clean layered architecture:

1. **API Layer** (`routes/`)
   - HTTP request/response handling
   - Input validation via Pydantic
   - Error handling and status codes
   - Dependency injection

2. **Business Logic Layer** (`rule_engine.py`)
   - Rule evaluation
   - Action execution
   - Real-time and retroactive processing

3. **Data Access Layer** (`crud_helpers.py`)
   - Common CRUD operations
   - Query building
   - Database interaction abstraction

4. **Database Layer** (`class_database.py`)
   - Connection management
   - Transaction handling
   - Schema initialization

5. **Schema/Validation Layer** (`schemas.py`)
   - Pydantic models
   - Input/output validation
   - Custom validators
   - Enum definitions

### Key Components

**Database (`class_database.py`)**
- Singleton instance created at startup
- Handles SQLite connection initialization
- Provides query execution, fetch, and commit methods
- Auto-creates schema on first run

**Dependency Injection (`get_db.py`)**
- FastAPI dependency for database access
- Allows test overrides with in-memory database

**CRUD Helpers (`crud_helpers.py`)**
- Reusable functions for common operations
- Timestamp management
- Dynamic SQL building

**Rule Engine (`rule_engine.py`)**
- Evaluates conditions against measurements
- Executes actions on matching rules
- Handles retroactive evaluation for historical data

---

## Testing

The project includes comprehensive tests covering:

- ✅ Happy path scenarios (create, read, update, delete)
- ✅ Input validation (missing fields, invalid types, invalid values)
- ✅ Error handling (404s, 400s, 422s)
- ✅ Edge cases (duplicate names, invalid limits, boundary values)
- ✅ Business logic (rule triggers, state management)
- ✅ Integration (end-to-end workflows)

### Test Files

- `test_devices.py` - Device CRUD and state management
- `test_measurements.py` - Measurement storage and queries
- `test_rules.py` - Rule creation, evaluation, and automation
- `test_health.py` - Health check endpoint

### Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_devices.py

# Single test
pytest tests/test_devices.py::test_post_devices_returns_created_id

# With coverage
pytest --cov=app --cov-report=html
```

---

## Known Limitations and Future Improvements

### Current Limitations

1. **Single condition type** - Rules only support measurement threshold conditions. Future versions could support:
   - Time-based conditions (e.g., "every 5 minutes")
   - Device state conditions (e.g., "if device X is ON")
   - Logical operators (AND, OR, NOT)

2. **Single action type** - Rules only support device state changes. Future versions could support:
   - HTTP webhooks
   - MQTT publishing
   - Email notifications
   - Multiple sequential actions

3. **No authentication/authorization** - Anyone with network access can control devices

4. **No persistence of action history** - Triggered actions aren't logged or queryable

5. **SQLite only** - Not suitable for high-concurrency scenarios. PostgreSQL support could be added.

6. **No foreign key constraints** - Rules can reference non-existent devices/measurements

### Planned Improvements

- [ ] Add UPDATE/DELETE endpoints for devices and measurements
- [ ] Add authentication layer (API keys or JWT)
- [ ] Add action history logging
- [ ] Add support for multiple condition types and operators
- [ ] Add support for more action types (webhooks, MQTT, email)
- [ ] Add database migration system for schema changes
- [ ] Add metrics/monitoring endpoints
- [ ] Add async rule evaluation (currently synchronous)
- [ ] Add batch measurement import endpoint
- [ ] Add GraphQL interface alongside REST

---

## Development

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies including dev tools
pip install -r requirements.txt

# Install additional dev tools (optional)
pip install black isort flake8

# Format code
black app/ tests/
isort app/ tests/

# Run linter
flake8 app/ tests/

# Type check
mypy app/
```

### Code Standards

- Python 3.11+ with type hints
- PEP 8 style guide
- Comprehensive logging for debugging
- All code should be tested

### Adding New Endpoints

1. Create schema models in `schemas.py`
2. Create route handler in `routes/`
3. Use database dependency injection
4. Add comprehensive tests
5. Document in this README

---

## Troubleshooting

### Database Connection Issues

**Problem**: `database is locked`
- **Cause**: Multiple processes writing to SQLite simultaneously
- **Solution**: Ensure only one Uvicorn process is running

### Type Errors with mypy

**Solution**: Run with ignore missing imports:
```bash
mypy app/ --ignore-missing-imports
```

### Tests Failing

**Problem**: Tests fail with import errors
- **Solution**: Ensure virtual environment is activated and dependencies installed:
  ```bash
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

### API Not Responding

**Problem**: Server crashes or doesn't start
- **Solution**: Check logs for errors:
  ```bash
  uvicorn app.main:app --reload
  ```
  Look for database initialization errors or import issues

---

## Performance Considerations

### Optimizations for Raspberry Pi

- SQLite is lightweight and suitable for small deployments
- Async FastAPI handles concurrent requests efficiently
- Pydantic validation happens in-process (no external service calls)
- Rule evaluation is efficient (O(n) where n = number of enabled rules)

### Scaling Considerations

If deploying at larger scale:

1. **Database**: Consider PostgreSQL instead of SQLite for better concurrency
2. **Caching**: Add Redis for measurement caching or rule condition caching
3. **Async Actions**: Move rule action execution to background queue (Celery/Rq)
4. **Measurement Batching**: Implement batch insert endpoint for bulk data
5. **Connection Pooling**: Use sqlalchemy with connection pooling

### Database Query Performance

- Device and rule lookups are O(1) by name (indexed)
- Measurement queries are O(n) but limited by pagination
- Latest measurement query could be optimized with database window functions

---

## License

See the [LICENSE](LICENSE) file for details.

---

## Contact & Support

For issues, questions, or suggestions, please open an issue in the repository.

---

## Changelog

### Version 1.0.0 (2024-06-02)
- Initial release
- Device management with state tracking
- Measurement ingestion and querying
- Automation rules with real-time and retroactive evaluation
- Comprehensive test coverage
- Full REST API with FastAPI

---

## Quick Reference

| Endpoint                | Method | Purpose                         |
|-------------------------|--------|---------------------------------|
| `/health`               | GET    | Health check                    |
| `/devices`              | POST   | Create device                   |
| `/devices`              | GET    | List devices                    |
| `/devices/{name}`       | GET    | Get device                      |
| `/devices/{name}/state` | POST   | Update device state             |
| `/measurements`         | POST   | Store measurement               |
| `/measurements`         | GET    | List measurements               |
| `/measurements/latest`  | GET    | Get latest per measurement name |
| `/rules`                | POST   | Create rule                     |
| `/rules`                | GET    | List rules                      |
| `/rules/{name}`         | GET    | Get rule                        |
| `/rules/{name}/toggle`  | POST   | Enable/disable rule             |
| `/rules/{name}`         | DELETE | Delete rule                     |