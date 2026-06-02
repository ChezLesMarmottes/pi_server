import logging
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
    
    cursor = db.execute(
        "UPDATE sensors SET state=? WHERE name=?",
        (rule["action_state"], rule["action_sensor"])
    )
    db.commit()
    
    if cursor.rowcount == 0:
        logger.warning(f"Rule '{rule['name']}' executed but sensor '{rule['action_sensor']}' not found")
    else:
        logger.info(f"Rule '{rule['name']}' executed")