import sqlite3
from typing import Annotated
from fastapi import Depends

def get_connection():
    #Define connection and cursor
    connection = sqlite3.connect("data/platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    try:
        yield connection, cursor
        
    finally:
        connection.close()

connection_dependency = Annotated[tuple, Depends(get_connection)]