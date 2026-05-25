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

### Health

#### `GET /health`

Returns a simple health check response.

**Response**

```json
{ "status": "ok" }
```

### Measurements

#### `GET /measurements`

Returns measurements from the database.

Query parameters:

* `name` (optional): filter measurements by name
* `limit` (optional, default: `20`): maximum number of results returned

Example:

```text
GET /measurements?name=temperature&limit=10
```

#### `POST /measurements`

Creates a new measurement entry.

This endpoint accepts a measurement input model (`MeasurementIn`) and stores it in the database.

#### `GET /measurements/latest`

Returns the most recent measurement entry.

### Devices

#### `GET /devices`

Returns all devices.

#### `POST /devices`

Creates a new device entry.

This endpoint accepts a device input model (`DeviceIn`) and stores it in the database.

#### `GET /devices/{name}`

Returns a single device by name.

#### `POST /devices/{name}/state`

Updates the state of the device with the given name.

Example:

```text
POST /devices/pump/state?state=on
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