import os
import sqlite3

from typing import Any

class Database:
    connection: sqlite3.Connection

    def __init__(self, db_path: str = "data/platform.db") -> None:
        db_dir = os.path.dirname(db_path)
        if db_path != ":memory:" and db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        cursor: sqlite3.Cursor = self.connection.cursor()

        cursor.execute("""             
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            name TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            timestamp TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            state TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            enabled INTEGER NOT NULL,
            condition_type TEXT NOT NULL,
            condition_measurement TEXT NOT NULL,
            condition_operator TEXT NOT NULL,
            condition_value REAL NOT NULL,
            action_type TEXT NOT NULL,
            action_device TEXT NOT NULL,
            action_state TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)

        self.connection.commit()

    def execute(self, query: str, values: tuple[str | int | float, ...] | None = None) -> sqlite3.Cursor:
        cursor: sqlite3.Cursor = self.connection.cursor()
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        return cursor

    def fetch_all(self, query: str, values: tuple[str | int | float, ...] | None = None) -> list[dict[Any, Any]]:
        cursor: sqlite3.Cursor = self.execute(query, values)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, values: tuple[str | int | float, ...] | None = None) -> dict[Any, Any] | None:
        cursor: sqlite3.Cursor = self.execute(query, values)
        result: sqlite3.Row | None = cursor.fetchone()
        return dict(result) if result is not None else None
    
    def commit(self) -> None:
        self.connection.commit()