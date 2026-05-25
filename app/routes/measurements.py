from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models import MeasurementIn, MeasurementOut
from app.database import connection_dependency

measurements_router = APIRouter()

@measurements_router.post("")
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn):
    connection, cursor = db

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
    if not result:
        raise HTTPException(404, detail="Device not found")

    return result

@measurements_router.get("")
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20):
    connection, cursor = db

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
    result = {"status": "ok", "data": [MeasurementOut(**row) for row in cursor.fetchall()]}
    if not result:
        raise HTTPException(404, detail="Device not found")

    return result

@measurements_router.get("/latest")
def get_measurements_latest(db: connection_dependency):
    connection, cursor = db

    cursor.execute("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")

    result = {"status": "ok", "data": [MeasurementOut(**row) for row in cursor.fetchall()]}
    if not result:
        raise HTTPException(404, detail="Device not found")

    return result