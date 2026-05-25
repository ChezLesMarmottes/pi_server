import sqlite3


def get_connection():
    #Define connection and cursor
    connection = sqlite3.connect("platform.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    return connection, cursor