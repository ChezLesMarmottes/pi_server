from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter
import sqlite3

from app.models import DevicesIn, DevicesOut
from app.main import app
from app.database import get_connection

devices_router = APIRouter()

@app.get("/devices")
def get_devices():
    connection, cursor = get_connection()

    #code

    connection.close()

    #return result

@app.post("/devices")
def post_devices():
    connection, cursor = get_connection()

    #code

    connection.close()

    #return result

@app.get("/devices/{name}")
def get_devices_name():
    connection, cursor = get_connection()

    #code

    connection.close()

    #return result

@app.post("/devices/{name}/state")
def post_devices_name_state():
    connection, cursor = get_connection()

    #code

    connection.close()

    #return result