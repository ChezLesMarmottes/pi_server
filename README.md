# PI Server

PI Server is a FastAPI-based REST API for managing digital **devices** and **measurements**. It uses SQLite for persistence and is intended to run on a Raspberry Pi or any local Python environment.

## Features

* Device creation, listing, retrieval, and state updates
* Measurement ingestion, paged history queries, and latest-per-name queries
* Pydantic request validation and structured JSON responses
* Automatic SQLite schema initialization
* Lightweight FastAPI application served with Uvicorn

## Tech stack

* Python
* FastAPI
* Pydantic
* SQLite
* Uvicorn
* Pytest

## Project structure

```text
pi_server/
├── app/
│   ├── routes/
│   │   ├── devices.py
│   │   ├── health.py
│   │   └── measurements.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── data/
│   └── platform.db
├── tests/
│   ├── conftest.py
│   ├── test_devices.py
│   ├── test_health.py
│   └── test_measurements.py
├── LICENSE
├── README.md
└── requirements.txt
```

## Database

The API stores data in SQLite at:

```text
data/platform.db
```

`app/models.py` defines a `Database` class that creates the required tables automatically on startup.

### Tables

#### `devices`

| Column    | Type    | Notes                          |
| --------- | ------- | ------------------------------ |
| id        | INTEGER | Primary key, autoincrement     |
| name      | TEXT    | Unique device name             |
| state     | TEXT    | Device state                   |
| timestamp | TEXT    | UTC ISO-8601 creation/update   |

#### `measurements`

| Column    | Type    | Notes                             |
| --------- | ------- | --------------------------------- |
| id        | INTEGER | Primary key, autoincrement        |
| source    | TEXT    | Measurement source identifier     |
| name      | TEXT    | Measurement name                  |
| value     | REAL    | Numeric measurement value         |
| unit      | TEXT    | Optional measurement unit         |
| timestamp | TEXT    | UTC ISO-8601 measurement time     |

## API Reference

All endpoints return JSON wrapped in an `ApiResponse` envelope.

### Health

#### `GET /health`

Returns a simple service health check.

**Response**

```json
{ "status": "ok" }
```

### Measurements

#### `POST /measurements`

Stores a new measurement record.

**Request body**

```json
{
  "source": "arduino_1",
  "name": "temperature",
  "value": 21.6,
  "unit": "C"
}
```

**Validation rules**

* `source` and `name` are required and must be non-empty
* `value` must be a finite number
* `unit` is optional

**Response**

```json
{
  "status": "ok",
  "message": "measurement stored",
  "data": {
    "id": 1
  }
}
```

#### `GET /measurements`

Returns a list of measurements ordered newest first.

**Query parameters**

* `name` (optional) — filter by measurement name
* `limit` (optional) — max rows returned, default `20`, must be between `1` and `99`

**Example**

```text
GET /measurements?name=temperature&limit=10
```

**Response**

```json
{
  "status": "ok",
  "data": [
    {
      "id": 12,
      "source": "arduino_1",
      "name": "temperature",
      "value": 21.6,
      "unit": "C",
      "timestamp": "2026-05-26T18:12:34.123456+00:00"
    }
  ]
}
```

#### `GET /measurements/latest`

Returns the latest measurement record for each distinct measurement `name`.

**Response**

```json
{
  "status": "ok",
  "data": [
    {
      "id": 12,
      "source": "arduino_1",
      "name": "temperature",
      "value": 21.6,
      "unit": "C",
      "timestamp": "2026-05-26T18:12:34.123456+00:00"
    }
  ]
}
```

### Devices

#### `POST /devices`

Creates a new device record.

**Request body**

```json
{
  "name": "pump",
  "state": "off"
}
```

**Validation rules**

* `name` and `state` are required and must be non-empty
* `name` must be unique

**Response**

```json
{
  "status": "ok",
  "message": "device created",
  "data": {
    "id": 1
  }
}
```

Duplicate names return HTTP `400`.

#### `GET /devices`

Returns a list of devices ordered newest first.

**Query parameters**

* `name` (optional) — filter by device name
* `limit` (optional) — max rows returned, default `20`, must be between `1` and `99`

**Response**

```json
{
  "status": "ok",
  "data": [
    {
      "id": 1,
      "name": "pump",
      "state": "off",
      "timestamp": "2026-05-26T18:12:34.123456+00:00"
    }
  ]
}
```

#### `GET /devices/{name}`

Returns the most recent device row for a given device name.

**Response**

```json
{
  "status": "ok",
  "data": {
    "id": 1,
    "name": "pump",
    "state": "off",
    "timestamp": "2026-05-26T18:12:34.123456+00:00"
  }
}
```

Missing devices return HTTP `404`.

#### `POST /devices/{name}/state`

Updates the state of an existing device.

**Query parameters**

* `state` — new device state

Supported states:

* `ON`
* `OFF`
* `ARMED`
* `READING`
* `READY`

**Response**

```json
{
  "status": "ok",
  "message": "state updated",
  "data": {
    "id": 1,
    "name": "pump",
    "state": "ON",
    "timestamp": "2026-05-26T18:12:34.123456+00:00"
  }
}
```

Invalid states return HTTP `400`, and missing devices return HTTP `404`.

## Data models

The application uses Pydantic models defined in `app/models.py`:

* `MeasurementIn`
* `MeasurementOut`
* `DeviceIn`
* `DeviceOut`
* `CreateData`

These models provide consistent validation and serialization for requests and responses.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing

Run the test suite with:

```bash
pytest -q
```

## Notes

* The SQLite database is initialized automatically when the app starts.
* `app/database.py` provides a shared database dependency for the FastAPI routes.
* This project is a digital prototype that can evolve toward hardware and sensor integration.

## License

See `LICENSE` for license information.
