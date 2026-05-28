from contextlib import asynccontextmanager
from fastapi import FastAPI
import sqlite3

from app.routes.measurements import measurements_router
from app.routes.devices import devices_router
from app.routes.health import health_router
import logging

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Start of program
    connection = sqlite3.connect("data/platform.db")
    cursor = connection.cursor()
    logger.info("Server started, connection and cursor created")

    #Create measurements table
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    name TEXT, 
                    value REAL,
                    unit TEXT,
                    timestamp TEXT
                    );""")
        logger.info("measurements table created")
    except Exception:
        logger.exception("Failed query: Couldn't create measurements table")
        raise
    
    #Create devices table
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    state TEXT,
                    timestamp TEXT
                    );""")
        logger.info("devices table created")
    except Exception:
        logger.exception("Failed query: Couldn't create devices table")
        raise

    connection.commit()
    connection.close()
    yield
    #End of program
    logger.info("Connection closed")

app = FastAPI(lifespan=lifespan)

app.include_router(measurements_router, prefix="/measurements")
app.include_router(devices_router, prefix="/devices")
app.include_router(health_router, prefix="/health")