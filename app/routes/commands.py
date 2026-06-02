import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.crud_helpers import insert_record, prepare_record_for_insert
from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, CommandIn, CommandOut, CommandStatus

commands_router: APIRouter = APIRouter()

logger: logging.Logger = logging.getLogger(__name__)


@commands_router.post("", response_model=ApiResponse[CreateData])
def post_command(db: connection_dependency, command_in: CommandIn) -> dict[str, str | dict[str, int]]:

    record: dict[str, Any] = prepare_record_for_insert(command_in.model_dump(mode="json"))
    record["status"] = CommandStatus.PENDING.value

    try:
        row_id: int = insert_record(db, "commands", record)
    except Exception:
        logger.exception("Failed query: Couldn't insert command")
        raise

    result: dict[str, str | dict[str, int]] = {"status": "ok", "message": "command created", "data": {"id": row_id}}

    return result


@commands_router.get("/pending", response_model=ApiResponse[list[CommandOut]])
def get_pending_commands(db: connection_dependency, limit: int = 20) -> dict[str, str | list[CommandOut]]:

    if not (1 <= limit < 100):
        raise HTTPException(400, detail="Limit must be between 1 and 99")

    try:
        rows: list[dict[str, Any]] = db.fetch_all(
            "SELECT * FROM commands WHERE status=? ORDER BY id ASC LIMIT ?",
            (CommandStatus.PENDING.value, limit)
        )
    except Exception:
        logger.exception("Failed query: Couldn't fetch pending commands")
        raise

    result: dict[str, str | list[CommandOut]] = {
        "status": "ok",
        "message": "got pending commands",
        "data": [CommandOut(**row) for row in rows]
    }

    return result


@commands_router.post("/{command_id}/ack", response_model=ApiResponse[CommandOut])
def acknowledge_command(db: connection_dependency, command_id: int) -> dict[str, str | CommandOut]:

    try:
        row: dict[str, Any] | None = db.fetch_one(
            "SELECT * FROM commands WHERE id=?",
            (command_id,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't fetch command")
        raise

    if row is None:
        raise HTTPException(404, detail="Command not found")

    acknowledged_at: str = datetime.now(timezone.utc).isoformat()

    try:
        db.execute(
            "UPDATE commands SET status=?, acknowledged_at=? WHERE id=?",
            (CommandStatus.ACKNOWLEDGED.value, acknowledged_at, command_id)
        )
        db.commit()
    except Exception:
        logger.exception("Failed query: Couldn't acknowledge command")
        raise

    try:
        updated_row: dict[str, Any] | None = db.fetch_one(
            "SELECT * FROM commands WHERE id=?",
            (command_id,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't fetch updated command")
        raise

    if updated_row is None:
        raise HTTPException(500, detail="Command disappeared after update")

    result: dict[str, str | CommandOut] = {
        "status": "ok",
        "message": "command acknowledged",
        "data": CommandOut(**updated_row)
    }

    return result


@commands_router.get("", response_model=ApiResponse[list[CommandOut]])
def get_commands(db: connection_dependency, limit: int = 50) -> dict[str, str | list[CommandOut]]:

    if not (1 <= limit < 200):
        raise HTTPException(400, detail="Limit must be between 1 and 199")

    try:
        rows: list[dict[str, Any]] = db.fetch_all(
            "SELECT * FROM commands ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    except Exception:
        logger.exception("Failed query: Couldn't fetch commands")
        raise

    result: dict[str, str | list[CommandOut]] = {
        "status": "ok",
        "message": "got commands",
        "data": [CommandOut(**row) for row in rows]
    }

    return result
