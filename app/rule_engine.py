import logging
from datetime import datetime, timezone
from typing import Any, Callable, cast

from app.class_database import Database

logger = logging.getLogger(__name__)

OPERATORS: dict[str, Callable[[float, float], bool]] = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def evaluate_rule(rule: dict[str, str | int | float], measurement: dict[str, str | int | float]) -> bool:

    if rule["condition_type"] != "measurement_threshold":
        return False
    if cast(str, rule["condition_measurement"]).lower() != cast(str, measurement["name"]).lower():
        return False
    
    operator = rule["condition_operator"]
    if operator not in OPERATORS:
        logger.error(f"Unknown operator: {operator}")
        return False
    
    operator_fn = OPERATORS[operator]
    return operator_fn(cast(float, measurement["value"]), cast(float, rule["condition_value"]))

def evaluate_rule_retroactively(db: Database, rule: dict[str, str | int | float]) -> int:

    count = 0
    measurements = db.fetch_all("SELECT * FROM measurements")
    
    for measurement in measurements:
        if evaluate_rule(rule, measurement):
            try:
                execute_rule_action(db, rule)
                count += 1
            except Exception as e:
                logger.error(f"Failed to execute rule retroactively: {e}")
    
    return count

def execute_rule_action(db: Database, rule: dict[str, str | int | float]) -> None:
  
    if rule["action_type"] != "set_sensor_state":
        return
    
    # Look up sensor by name to get its ID
    sensor_row: dict[str, Any] | None = db.fetch_one(
        "SELECT id FROM sensors WHERE name=?",
        (rule["action_sensor"],)
    )
    
    if sensor_row is None:
        logger.warning(f"Rule '{rule['name']}' executed but sensor '{rule['action_sensor']}' not found")
        return
    
    sensor_id: int = sensor_row["id"]
    action: str = cast(str, rule["action_state"])
    
    # Create a command for the hardware bridge to execute
    try:
        cursor = db.execute(
            "INSERT INTO commands (sensor_id, action, status, timestamp) VALUES (?, ?, ?, ?)",
            (sensor_id, action, "pending", datetime.now(timezone.utc).isoformat())
        )
        db.commit()
        logger.info(f"Rule '{rule['name']}' created command for sensor '{rule['action_sensor']}' with action '{action}'")
    except Exception as e:
        logger.error(f"Failed to create command from rule: {e}")
        raise
    
    # Also update sensor state for backward compatibility (for non-Arduino sensors)
    try:
        db.execute(
            "UPDATE sensors SET state=? WHERE name=?",
            (action, rule["action_sensor"])
        )
        db.commit()
        logger.info(f"Rule '{rule['name']}' updated sensor state to {action}")
    except Exception as e:
        logger.error(f"Failed to update sensor state: {e}")