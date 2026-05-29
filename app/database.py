from typing import Annotated
from fastapi import Depends

from app.models import Database

db = Database()

def get_db() -> Database:
    return db

connection_dependency = Annotated[Database, Depends(get_db)]