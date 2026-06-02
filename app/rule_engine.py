import logging

from app.class_database import Database

logger = logging.getLogger(__name__)

OPERATORS = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def evaluate_rule(rule: dict, measurement: dict) -> bool:

    if rule["condition_type"] != "measurement_threshold":
        return False
    if rule["condition_measurement"].lower() != measurement["name"].lower():
        return False
    
    operator = rule["condition_operator"]
    if operator not in OPERATORS:
        logger.error(f"Unknown operator: {operator}")
        return False
    
    operator_fn = OPERATORS[operator]
    return operator_fn(measurement["value"], rule["condition_value"])

def evaluate_rule_retroactively(db: Database, rule: dict) -> int:

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

def execute_rule_action(db: Database, rule: dict) -> None:
  
    if rule["action_type"] != "set_device_state":
        return
    
    cursor = db.execute(
        "UPDATE devices SET state=? WHERE name=?",
        (rule["action_state"], rule["action_device"])
    )
    db.commit()
    
    if cursor.rowcount == 0:
        logger.warning(f"Rule '{rule['name']}' executed but device '{rule['action_device']}' not found")
    else:
        logger.info(f"Rule '{rule['name']}' executed")