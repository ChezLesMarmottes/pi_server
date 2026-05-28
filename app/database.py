from typing import Annotated
from fastapi import Depends

from app.models import Database

def get_connection():
    db = Database()

    try:
        yield db
        
    finally:
        db.connection.close()

connection_dependency = Annotated[Database, Depends(get_connection)]