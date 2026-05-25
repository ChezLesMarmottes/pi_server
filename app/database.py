from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
import sqlite3

from app.models import *
from app.routes.measurements import measurements_router
from app.routes.devices import devices_router

def get_connection():
    #Define connection and cursor
    connection = sqlite3.connect("platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return connection, cursor