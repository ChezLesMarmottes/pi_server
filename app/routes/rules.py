from datetime import datetime, timezone
import logging
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException

from app.get_db import connection_dependency
from app.schemas import ApiResponse, CreateData, RuleEnabledIn, RuleIn, RuleOut

rules_router: APIRouter = APIRouter()

@rules_router.post("", response_model=ApiResponse[CreateData])
def post_rules(db: connection_dependency, rule_in: RuleIn): #-> dict[str, str | dict[str, int]]:
    pass

@rules_router.get("", response_model=ApiResponse[list[RuleOut]])
def get_rules(db: connection_dependency, name: str | None = None, limit: int = 20): #-> dict[str, list[DeviceOut]]:
    pass

@rules_router.post("/{name}/toggle", response_model=ApiResponse[RuleOut])
def post_name_toggle(db: connection_dependency, name: str, toggle_in: RuleEnabledIn): #-> dict[str, str | DeviceOut]:
    pass

@rules_router.delete("/{name}", response_model=ApiResponse[RuleOut])
def delete_name(db: connection_dependency, name: str): #->dict[str, RuleOut]
    pass