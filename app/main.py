from contextlib import asynccontextmanager
from fastapi import FastAPI
import sqlite3

from app.models import *
from app.routes.measurements import measurements_router
from app.routes.devices import devices_router
from app.routes.health import health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = sqlite3.connect("data/platform.db")
    cursor = connection.cursor()

    #Create measurements db
    cursor.execute("""CREATE TABLE IF NOT EXISTS measurements (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               source TEXT,
               name TEXT, 
               value REAL,
               unit TEXT,
               timestamp TEXT
               );""")
    
    #Create devices db
    cursor.execute("""CREATE TABLE IF NOT EXISTS devices (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE,
                   state TEXT,
                   timestamp TEXT
                   );""")

    connection.commit()
    connection.close()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(measurements_router, prefix="/measurements")
app.include_router(devices_router, prefix="/devices")
app.include_router(health_router, prefix="/health")