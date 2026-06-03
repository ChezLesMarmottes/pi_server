import logging
import time
import sys
from types import ModuleType
from typing import Any

serial_module: ModuleType | None

try:
    import serial as serial_module
except ImportError:
    serial_module = None

SERIAL_AVAILABLE = serial_module is not None

import requests

logger = logging.getLogger(__name__)


class SerialBridge:
    """
    Hardware bridge that connects to an Arduino via serial port.
    
    Protocol:
    - Incoming: MEASURE:sensor_id:value
    - Outgoing: COMMAND:sensor_id:action
    """

    def __init__(
        self,
        port: str = "/dev/ttyACM0",
        baudrate: int = 9600,
        api_base_url: str = "http://localhost:8000",
        command_poll_interval: float = 2.0,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.api_base_url = api_base_url
        self.command_poll_interval = command_poll_interval
        self.serial_connection: Any = None
        self.last_command_poll: float = 0.0
        self.running = False

    def connect(self) -> bool:
        """
        Connect to the serial port.
        Falls back to stdin if serial is not available (for testing).
        """
        if serial_module is None:
            logger.warning("pyserial not available, using stdin for testing")
            return True

        try:
            self.serial_connection = serial_module.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
            )
            logger.info(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from serial port."""
        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
                logger.info("Disconnected from serial port")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            self.serial_connection = None

    def read_line(self) -> str | None:
        """
        Read a line from serial or stdin.
        Returns None if no data available or on error.
        """
        try:
            if SERIAL_AVAILABLE and self.serial_connection is not None:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode("utf-8").strip()
                    return line if line else None
            else:
                # For testing without real serial
                return None
            return None
        except Exception as e:
            logger.error(f"Error reading from serial: {e}")
            return None

    def send_line(self, line: str) -> bool:
        """
        Send a line to serial port.
        Returns True if successful, False otherwise.
        """
        try:
            if SERIAL_AVAILABLE and self.serial_connection is not None:
                self.serial_connection.write((line + "\n").encode("utf-8"))
                self.serial_connection.flush()
                logger.debug(f"Sent to Arduino: {line}")
                return True
            else:
                logger.debug(f"Would send to Arduino: {line}")
                return True
        except Exception as e:
            logger.error(f"Error writing to serial: {e}")
            return False

    def parse_measurement(self, line: str) -> dict[str, Any] | None:
        """
        Parse a measurement line: MEASURE:sensor_id:value
        Returns dict with sensor_id and value, or None if parse fails.
        """
        try:
            parts = line.split(":")
            if len(parts) < 3 or parts[0].upper() != "MEASURE":
                return None

            sensor_id_str = parts[1].strip()
            value_str = parts[2].strip()

            sensor_id = int(sensor_id_str)
            value = float(value_str)

            return {"sensor_id": sensor_id, "value": value}
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse measurement '{line}': {e}")
            return None

    def handle_measurement(self, measurement: dict[str, Any]) -> bool:
        """
        Handle an incoming measurement by sending it to the API.
        Returns True if successful, False otherwise.
        """
        try:
            sensor_id = measurement["sensor_id"]
            value = measurement["value"]

            # Get sensor name from database via API
            response = requests.get(
                f"{self.api_base_url}/sensors",
                timeout=5.0,
            )
            if response.status_code != 200:
                logger.error(f"Failed to get sensors: {response.status_code}")
                return False

            data = response.json()
            sensors = data.get("data", [])

            # Find sensor by ID
            sensor_name = None
            for sensor in sensors:
                if sensor["id"] == sensor_id:
                    sensor_name = sensor["name"]
                    break

            if sensor_name is None:
                logger.warning(f"Sensor with id {sensor_id} not found")
                return False

            # Post measurement
            measurement_payload = {
                "source": "arduino",
                "name": sensor_name,
                "value": value,
                "unit": None,
            }

            response = requests.post(
                f"{self.api_base_url}/measurements",
                json=measurement_payload,
                timeout=5.0,
            )

            if response.status_code == 200:
                logger.info(f"Stored measurement: {sensor_name}={value}")
                return True
            else:
                logger.error(f"Failed to store measurement: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error handling measurement: {e}")
            return False

    def poll_and_send_commands(self) -> None:
        """
        Poll API for pending commands and send them to Arduino.
        """
        current_time = time.time()
        if current_time - self.last_command_poll < self.command_poll_interval:
            return

        self.last_command_poll = current_time

        try:
            response = requests.get(
                f"{self.api_base_url}/commands/pending",
                timeout=5.0,
            )

            if response.status_code != 200:
                logger.warning(f"Failed to get pending commands: {response.status_code}")
                return

            data = response.json()
            commands = data.get("data", [])

            for command in commands:
                command_id = command["id"]
                sensor_id = command["sensor_id"]
                action = command["action"]

                # Send command to Arduino
                command_line = f"COMMAND:{sensor_id}:{action}"
                if self.send_line(command_line):
                    # Acknowledge command
                    try:
                        ack_response = requests.post(
                            f"{self.api_base_url}/commands/{command_id}/ack",
                            timeout=5.0,
                        )
                        if ack_response.status_code == 200:
                            logger.info(f"Sent and acknowledged command {command_id}: {command_line}")
                        else:
                            logger.warning(f"Failed to acknowledge command {command_id}: {ack_response.status_code}")
                    except Exception as e:
                        logger.error(f"Error acknowledging command: {e}")
                else:
                    logger.error(f"Failed to send command to Arduino: {command_line}")

        except Exception as e:
            logger.error(f"Error polling commands: {e}")

    def run(self) -> None:
        """
        Main loop for the hardware bridge.
        """
        if not self.connect():
            logger.error("Failed to connect to hardware")
            return

        self.running = True
        logger.info("Hardware bridge started")

        try:
            while self.running:
                # Read incoming measurements
                line = self.read_line()
                if line:
                    logger.debug(f"Received from Arduino: {line}")
                    measurement = self.parse_measurement(line)
                    if measurement:
                        self.handle_measurement(measurement)
                    else:
                        logger.debug(f"Could not parse line: {line}")

                # Poll and send commands periodically
                self.poll_and_send_commands()

                # Small sleep to prevent busy-waiting
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Hardware bridge interrupted")
        except Exception as e:
            logger.error(f"Hardware bridge error: {e}")
        finally:
            self.disconnect()
            self.running = False
            logger.info("Hardware bridge stopped")

    def stop(self) -> None:
        """Stop the hardware bridge."""
        self.running = False


def main() -> None:
    """
    Entry point for the hardware bridge daemon.
    """
    import argparse

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description="Hardware bridge for Arduino communication")
    parser.add_argument("--port", default="/dev/ttyACM0", help="Serial port (default: /dev/ttyACM0)")
    parser.add_argument("--baudrate", type=int, default=9600, help="Baud rate (default: 9600)")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="Command poll interval in seconds")

    args = parser.parse_args()

    bridge = SerialBridge(
        port=args.port,
        baudrate=args.baudrate,
        api_base_url=args.api_url,
        command_poll_interval=args.poll_interval,
    )

    bridge.run()


if __name__ == "__main__":
    main()
