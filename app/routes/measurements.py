from datetime import datetime, timezone
from fastapi import APIRouter

from app.models import MeasurementIn, MeasurementOut
from app.database import get_connection

measurements_router = APIRouter()

@measurements_router.post("")
def post_measurements(measurement_in: MeasurementIn):
    connection, cursor = get_connection()

    #Log 1
    print(f"IN: {measurement_in}")

    record = {}

    record.update(measurement_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO measurements ({columns}) VALUES ({placeholders});"

    cursor.execute(query, values)
    connection.commit()

    #Log 2
    print(f"OUT: {record}")

    cursor.execute("SELECT * FROM measurements WHERE id=?", (cursor.lastrowid,))

    result = {"status": "ok", "message": "measurement stored", "id": cursor.lastrowid}

    connection.close()

    return result

@measurements_router.get("")
def get_measurements(name: str | None = None, limit: int = 20):
    connection, cursor = get_connection()

    conditions = []
    values = []

    if name:
        conditions.append("name=?")
        values.append(name)
    
    query = "SELECT * FROM measurements " 
    if conditions:
        query += "WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    cursor.execute(query, values)
    result = [MeasurementOut(**row) for row in cursor.fetchall()]

    connection.close()

    return result

@measurements_router.get("/latest")
def get_measurements_latest():
    connection, cursor = get_connection()

    cursor.execute("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")

    result = {"status": "ok", "data": [MeasurementOut(**row) for row in cursor.fetchall()]}

    connection.close()

    return result