# PI Server

A FastAPI-based API server running on a Raspberry Pi, backed by SQLite. This project is the first digital phase of a larger home-lab / embedded system: devices and measurements are represented digitally for now, with an Arduino and physical sensors planned for later integration.

## Overview

PI Server exposes a small REST API for managing **devices** and **measurements**. It currently runs locally on a Raspberry Pi and stores all persistent data in a SQLite database.

The current implementation is fully digital:

* **Devices** are the digital analogue of future physical devices / sensor nodes.
* **Measurements** are the digital analogue of future sensor readings.

The API uses Pydantic models for request and response validation and is served with Uvicorn.

## Tech stack

* Python
* FastAPI
* Uvicorn
* SQLite
* Pydantic
* Virtual environment (`venv`)

## Project structure

```text
pi_server/
├── venv/
├── app/
│   ├── routes/
│   │   ├── devices.py
│   │   ├── measurements.py
│   │   └── health.py
│   ├── database.py
│   ├── main.py
│   └── models.py
├── data/
│   └── platform.db
├── .gitignore
├── requirements.txt
└── README.md
```

## Database

The application uses a SQLite database stored at:

```text
data/platform.db
```

The database and tables are created during application startup.

### Tables

#### `devices`

| Column    | Type    | Notes                          |
| --------- | ------- | ------------------------------ |
| id        | INTEGER | Primary key, autoincrement     |
| name      | TEXT    | Unique device name             |
| state     | TEXT    | Current device state           |
| timestamp | TEXT    | Timestamp of creation / update |

#### `measurements`

| Column    | Type    | Notes                        |
| --------- | ------- | ---------------------------- |
| id        | INTEGER | Primary key, autoincrement   |
| source    | TEXT    | Source of the measurement    |
| name      | TEXT    | Measurement name             |
| value     | REAL    | Numeric value                |
| unit      | TEXT    | Unit of the value            |
| timestamp | TEXT    | Timestamp of the measurement |

## API endpoints

All endpoints return JSON. Responses follow a simple envelope style with a `status` field and, depending on the endpoint, either `message`, `id`, `data`, or `device`.

### Health

#### `GET /health`

Health check endpoint used to confirm that the API is running.

**Response**

```json
{
  "status": "ok"
}
```

---

### Measurements

#### `POST /measurements`

Stores a new measurement in the `measurements` table.

**Request body**

* JSON object matching `MeasurementIn`
* The exact fields are defined in `app/models.py`
* The server automatically adds a UTC ISO-8601 `timestamp`

**Behavior**

* Logs the incoming model to stdout
* Inserts the measurement into SQLite
* Commits the transaction
* Returns the newly inserted row id

**Response**

```json
{
  "status": "ok",
  "message": "measurement stored",
  "id": 1
}
```

#### `GET /measurements`

Returns a list of measurements, newest first.

**Query parameters**

* `name` (optional): filters results by measurement name
* `limit` (optional, default: `20`): maximum number of rows returned

**Examples**

```text
GET /measurements
GET /measurements?name=temperature
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

Returns the latest measurement for each measurement name.

This endpoint is useful when you want the current/latest state for all measurement types without requesting the full history.

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

---

### Devices

#### `POST /devices`

Creates a new device entry in the `devices` table.

**Request body**

* JSON object matching `DeviceIn`
* The exact fields are defined in `app/models.py`
* The server automatically adds a UTC ISO-8601 `timestamp`

**Behavior**

* Logs the incoming model to stdout
* Inserts the device into SQLite
* Commits the transaction
* Returns the newly inserted row id

**Response**

```json
{
  "status": "ok",
  "message": "device created",
  "id": 1
}
```

#### `GET /devices`

Returns a list of devices, newest first.

**Query parameters**

* `name` (optional): filters results by device name
* `limit` (optional, default: `20`): maximum number of rows returned

**Examples**

```text
GET /devices
GET /devices?name=pump
GET /devices?name=pump&limit=5
```

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

Returns the most recent record for a single device by name.

**Path parameters**

* `name`: device name

**Example**

```text
GET /devices/pump
```

**Response**

```json
{
  "status": "ok",
  "device": {
    "id": 1,
    "name": "pump",
    "state": "off",
    "timestamp": "2026-05-26T18:12:34.123456+00:00"
  }
}
```

#### `POST /devices/{name}/state`

Updates the `state` of an existing device.

**Path parameters**

* `name`: device name

**Query parameters**

* `state`: new device state

**Example**

```text
POST /devices/pump/state?state=on
```

**Behavior**

* Updates the matching device row by name
* Returns `404` if no device matches
* Commits the transaction so later GET requests see the new state

**Response**

```json
{
  "status": "ok",
  "message": "state updated",
  "device": {
    "id": 1,
    "name": "pump",
    "state": "on",
    "timestamp": "2026-05-26T18:12:34.123456+00:00"
  }
}
```

## Data models

The project uses Pydantic models for validation and serialization.

* `MeasurementIn`
* `MeasurementOut`
* `DeviceIn`
* `DeviceOut`

These models define the shape of incoming request bodies and outgoing API responses.

## Running locally

### 1. Activate the virtual environment

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Development notes

* The project currently has no authentication.
* Logging is minimal for now, but the codebase is intended to expand using Python's `logging` module.
* The system is designed to evolve from a digital API into a physical Pi + Arduino + sensor setup.

## Planned direction

This project is part one of a larger embedded / IoT system. The long-term goal is to connect the API layer to real hardware so that:

* devices correspond to physical components
* measurements are collected from actual sensors
* the Raspberry Pi acts as the central server / data layer
* an Arduino or similar microcontroller handles sensor-side interaction

## License

No license has been defined yet.