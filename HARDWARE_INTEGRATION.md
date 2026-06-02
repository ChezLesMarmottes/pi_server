# Hardware Integration Guide

## Overview

This guide explains how to set up and use the hardware bridge to connect an Arduino to the Pi Server API.

## Architecture

```
Arduino (with sensors/actuators)
    ↓ (Serial: MEASURE:sensor_id:value)
Serial Port (/dev/ttyUSB0)
    ↓
Hardware Bridge Daemon (serial_bridge.py)
    ↓ (HTTP)
FastAPI (Raspberry Pi)
    ↓
Database
```

## Setup Steps

### 1. Register Sensors in the API

First, create sensor entities in your API:

```bash
# Create a temperature sensor
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "temperature_sensor_1", "state": "OFF"}'

# Create an LED actuator
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "led_1", "state": "OFF"}'
```

Note the sensor IDs returned. You'll use these in the Arduino code.

### 2. Configure Hardware Pins

Register which Arduino pins correspond to which sensors:

```bash
# Configure A0 pin to temperature_sensor_1 (id=1)
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 1,
    "arduino_pin": "A0",
    "pin_type": "analog",
    "read_interval_ms": 5000
  }'

# Configure D5 pin to led_1 (id=2)
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 2,
    "arduino_pin": "D5",
    "pin_type": "digital",
    "read_interval_ms": 1000
  }'
```

### 3. Arduino Code Example

```cpp
#define TEMP_SENSOR_PIN A0
#define LED_PIN 5
#define SENSOR_ID_TEMP 1
#define SENSOR_ID_LED 2

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  // Read temperature sensor every 5 seconds
  static unsigned long lastTempRead = 0;
  if (millis() - lastTempRead >= 5000) {
    int rawValue = analogRead(TEMP_SENSOR_PIN);
    float voltage = rawValue * (5.0 / 1023.0);
    float celsius = (voltage - 0.5) * 100;  // For LM35 sensor
    
    Serial.print("MEASURE:");
    Serial.print(SENSOR_ID_TEMP);
    Serial.print(":");
    Serial.println(celsius);
    
    lastTempRead = millis();
  }
  
  // Check for incoming commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    
    if (command.startsWith("COMMAND:")) {
      // Parse: COMMAND:device_id:action
      int firstColon = command.indexOf(':');
      int secondColon = command.indexOf(':', firstColon + 1);
      
      int deviceId = command.substring(firstColon + 1, secondColon).toInt();
      String action = command.substring(secondColon + 1);
      
      if (deviceId == SENSOR_ID_LED) {
        if (action == "ON") {
          digitalWrite(LED_PIN, HIGH);
        } else if (action == "OFF") {
          digitalWrite(LED_PIN, LOW);
        }
      }
    }
  }
  
  delay(100);
}
```

### 4. Start the Hardware Bridge

```bash
# From the project root
python -m app.hardware.serial_bridge \
  --port /dev/ttyUSB0 \
  --baudrate 9600 \
  --api-url http://localhost:8000 \
  --poll-interval 2.0
```

**Options:**
- `--port`: Serial port (default: /dev/ttyUSB0)
- `--baudrate`: Baud rate (default: 9600)
- `--api-url`: API base URL (default: http://localhost:8000)
- `--poll-interval`: How often to check for pending commands in seconds (default: 2.0)

### 5. Start the API

```bash
uvicorn app.main:app --reload
```

### 6. Create an Automation Rule

Now you can create rules that trigger commands:

```bash
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "temp_warning",
    "enabled": true,
    "condition_type": "measurement_threshold",
    "condition_measurement": "temperature_sensor_1",
    "condition_operator": ">",
    "condition_value": 25.0,
    "action_type": "set_sensor_state",
    "action_sensor": "led_1",
    "action_state": "ON"
  }'
```

Now whenever the temperature exceeds 25°C:
1. The API stores the measurement
2. The rule evaluates to true
3. A command is created: `turn ON led_1`
4. The hardware bridge sends to Arduino: `COMMAND:2:ON`
5. The LED physically turns on

## Serial Protocol

### Message Format

All messages are newline-terminated text.

### From Arduino to Server

```
MEASURE:sensor_id:value
```

Example:
```
MEASURE:1:23.5
MEASURE:2:1023
```

### From Server to Arduino

```
COMMAND:sensor_id:action
```

Example:
```
COMMAND:2:ON
COMMAND:3:OFF
```

## API Endpoints

### Hardware Configuration

- `POST /hardware` - Create pin mapping
- `GET /hardware` - List all mappings
- `GET /hardware/{sensor_id}` - Get mapping for specific sensor

### Commands

- `POST /commands` - Create a command (usually done by rules)
- `GET /commands/pending` - Get pending commands (called by hardware bridge)
- `POST /commands/{command_id}/ack` - Acknowledge a command (called by hardware bridge)
- `GET /commands` - List all commands

## Troubleshooting

### Hardware bridge fails to connect

- Check serial port: `ls /dev/tty*`
- Verify Arduino is connected: `dmesg | tail`
- Try different baudrate (common: 9600, 115200)
- Check USB cable and connection

### Measurements not appearing

- Verify Arduino is sending data: `screen /dev/ttyUSB0 9600`
- Check hardware bridge logs for parsing errors
- Verify sensor IDs match between Arduino code and database
- Confirm API is running and accessible

### Commands not reaching Arduino

- Check pending commands: `curl http://localhost:8000/commands/pending`
- Verify hardware bridge poll interval isn't too long
- Check Arduino serial monitoring for incoming COMMAND messages
- Verify pin configuration matches Arduino code

### State mismatch

If the API says LED is ON but it's actually OFF:
- Check the command was actually sent to Arduino
- Verify Arduino code correctly interprets the action
- Look for Arduino crashes or resets

## Testing Without Hardware

To test without real hardware, the hardware bridge can accept input from stdin:

```bash
# Terminal 1: Start the API
uvicorn app.main:app --reload

# Terminal 2: Start hardware bridge (uses stdin)
python -m app.hardware.serial_bridge

# Terminal 3: Send test measurements
# Type messages like: MEASURE:1:23.5
```

## Performance Considerations

- **Command poll interval**: Lower = faster response (< 2s), but more API requests
- **Read interval on Arduino**: Configure based on sensor needs
- **Serial baud rate**: Higher = faster, but must match between Arduino and bridge
- **Number of sensors**: Each sensor adds one line per read interval; test with your full sensor count

## Future Enhancements

- CRC checksums for reliability
- Heartbeat messages to detect disconnections
- Command priorities
- Sensor calibration data
- Data buffering during disconnections
