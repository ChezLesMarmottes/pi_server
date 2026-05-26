from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.models import ApiResponse, MeasurementIn, MeasurementOut, CreateData
from app.database import connection_dependency

measurements_router = APIRouter()

@measurements_router.post("", response_model=ApiResponse[CreateData])
def post_measurements(db: connection_dependency, measurement_in: MeasurementIn):
    connection, cursor = db

    #Log 1
    print(f"IN: {measurement_in}")

    record: dict[str, str | int | float] = {}

    record.update(measurement_in.model_dump())
    record["timestamp"] = datetime.now(timezone.utc).isoformat()

    columns = ", ".join(record.keys())
    placeholders = ", ".join(["?"] * len(record))
    values = tuple(record.values())

    query = f"INSERT INTO measurements ({columns}) VALUES ({placeholders});"

    cursor.execute(query, values)
    if cursor.lastrowid is None:
        raise HTTPException(404, detail="Measurement not found")
    
    connection.commit()

    #Log 2
    print(f"OUT: {record}")

    result = {"message": "measurement stored", "data": {"id": cursor.lastrowid}}

    return result

@measurements_router.get("", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements(db: connection_dependency, name: str | None = None, limit: int = 20):
    _, cursor = db

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    conditions: list[str] = []
    values: list [str | int] = []

    if name:
        conditions.append("name=?")
        values.append(name)
    
    query = "SELECT * FROM measurements " 
    if conditions:
        query += "WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    values.append(limit)

    cursor.execute(query, values)
    
    result = {"data": [MeasurementOut(**row) for row in cursor.fetchall()]}

    return result

@measurements_router.get("/latest", response_model=ApiResponse[list[MeasurementOut]])
def get_measurements_latest(db: connection_dependency):
    _, cursor = db

    cursor.execute("SELECT * FROM measurements WHERE id IN (SELECT MAX(id) FROM measurements GROUP BY name) ORDER BY id DESC")
    rows = cursor.fetchall()
    if not rows:
        raise HTTPException(404, detail="Device not found")

    result = {"data": [MeasurementOut(**row) for row in rows]}

    return result