# Hardware Integration Guide

## Overview

This guide explains how to connect an Arduino with sensors and actuators to the Pi Server API. The system allows the Arduino to send real sensor readings to the API, which automatically triggers automation rules.

## Architecture

Data flows in two directions:

```
1. MEASUREMENTS (Arduino → API):
   Arduino (reads sensor pins) 
     → Serial Port (/dev/ttyACM0) 
     → Hardware Bridge (serial_bridge.py) 
     → HTTP POST to API (/measurements endpoint)
     → Database

2. COMMANDS (API → Arduino):
   Rule triggers 
     → API creates command
     → Hardware Bridge polls for commands (/commands/pending)
     → Hardware Bridge sends via serial
     → Arduino receives and executes
```

## Prerequisites

- Arduino board with sensors/actuators connected to pins
- USB cable connecting Arduino to Raspberry Pi
- Python environment with dependencies installed (`pip install -r requirements.txt`)
- The Pi Server API running (`uvicorn app.main:app`)

---

## Setup Steps (In Order)

### Step 1: Start the API Server

**What this does:** Starts the FastAPI server that will receive measurements and send commands to the Arduino.

**How to do it:**
```bash
cd /home/keess/dev/projects/python/pi_server
uvicorn app.main:app
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The API is now running and listening for HTTP requests on `http://localhost:8000`. Leave this terminal open.

---

### Step 2: Register Your Sensors in the Database

**What this does:** Creates logical sensor entities in the database so the system knows which sensors exist. Each sensor gets a unique ID that you'll reference in your Arduino code.

**Why it matters:** The API needs to know about every sensor before measurements arrive. The sensor ID links your Arduino code to the database.

**How to do it:** Open a new terminal and run these commands (replace sensor names with yours):

```bash
# Create a temperature sensor (DHT11)
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "temperature_dht11_1", "state": "OFF"}'
```

**Expected response:**

```json
{
  "status": "ok",
  "message": "sensor created",
  "data": {"id": 1}
}
```

**Important:** Note the returned `id`. In this example, it's `1`. You'll use this ID in your Arduino code.

Create any additional sensors you need:

```bash
# Create an LED actuator (something you want to control)
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "led_1", "state": "OFF"}'
```

Expected response:

```json
{
  "status": "ok",
  "message": "sensor created",
  "data": {"id": 2}
}
```

**Common sensors:**

* Temperature sensor → `"name": "temperature_dht11_1"`
* LED → `"name": "led_1"`
* Motion sensor → `"name": "motion_detector"`
* Fan → `"name": "cooling_fan"`

---

### Step 3: Register Hardware Pin Mappings

**What this does:** Tells the system which Arduino pins your sensors are connected to. This is the bridge between logical sensors and physical pins.

**Why it matters:** The hardware bridge needs to know:

* Which pin is the temperature sensor on? (A0, A1, D2, etc.)
* Is it analog or digital?
* How often should it be read?

**How to do it:** For each sensor, create a hardware config entry using its ID from Step 2:

```bash
# Example: temperature_dht11_1 (id=1) is connected to pin D2 (digital), read every 5 seconds
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 1,
    "arduino_pin": "D2",
    "pin_type": "digital",
    "read_interval_ms": 5000
  }'
```

**Expected response:**

```json
{
  "status": "ok",
  "message": "hardware config created",
  "data": {"id": 1}
}
```

**Field explanations:**

* `sensor_id`: The ID from Step 2 (e.g., `1` for temperature_dht11_1)
* `arduino_pin`: The physical Arduino pin (A0-A5 for analog, D0-D53 for digital on Mega)
* `pin_type`: Either `"analog"` or `"digital"`
* `read_interval_ms`: How often to read this pin in milliseconds (1000 = 1 second, 5000 = 5 seconds)

**Add another hardware config for your LED:**

```bash
# Example: led_1 (id=2) is on digital pin 5, read interval is 1 second
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 2,
    "arduino_pin": "D5",
    "pin_type": "digital",
    "read_interval_ms": 1000
  }'
```

**Verify your setup so far:**

```bash
# List all hardware configs
curl http://localhost:8000/hardware
```

You should see both configs listed.

---

### Step 4: Write and Flash Your Arduino Code

**What this does:** Programs your Arduino to read sensors and communicate with the hardware bridge via serial.

**Why it matters:** The Arduino is the physical layer. It needs to:
- Read sensor pins at configured intervals
- Send measurements in the correct format: `MEASURE:sensor_id:value`
- Listen for commands and execute them

**How to do it:** Use the Arduino IDE and upload this code to your board. **Replace the pin numbers and sensor IDs with yours from Steps 2 and 3:**

```cpp
#include "DHT.h"

// ====== CONFIGURATION ======
#define DHTPIN 2                  // DHT11 data pin connected to D2
#define DHTTYPE DHT11

#define LED_PIN 5
#define SENSOR_ID_TEMP 1
#define SENSOR_ID_LED 2
#define BAUD_RATE 9600
// ====== END CONFIGURATION ======

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  dht.begin();
}

void loop() {
  static unsigned long lastTempRead = 0;

  // ===== SEND MEASUREMENTS =====
  if (millis() - lastTempRead >= 5000) {
    float celsius = dht.readTemperature();

    if (!isnan(celsius)) {
      Serial.print("MEASURE:");
      Serial.print(SENSOR_ID_TEMP);
      Serial.print(":");
      Serial.println(celsius);
    } else {
      Serial.println("ERROR:DHT_READ_FAIL");
    }

    lastTempRead = millis();
  }

  // ===== RECEIVE AND EXECUTE COMMANDS =====
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');

    if (command.startsWith("COMMAND:")) {
      int firstColon = command.indexOf(':');
      int secondColon = command.indexOf(':', firstColon + 1);

      int sensorId = command.substring(firstColon + 1, secondColon).toInt();
      String action = command.substring(secondColon + 1);

      if (sensorId == SENSOR_ID_LED) {
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

**Key points:**
- Line 3-4: Change `A0` and `5` to match your actual pins
- Line 5-6: Use the sensor IDs from Step 2
- The format `MEASURE:1:23.5` means: "This is a measurement, from sensor 1, with value 23.5"
- The format `COMMAND:2:ON` means: "Execute command for sensor 2, turn it ON"

---

### Step 5: Verify Serial Connection

**What this does:** Confirms the Arduino is connected and communicating properly.

**How to do it:** Identify which serial port your Arduino is on:

```bash
# Linux/Mac: List all serial devices
ls /dev/tty*

# You'll see something like /dev/ttyACM0 or /dev/ttyACM0
```

The most recent one is likely your Arduino. If unsure, unplug the Arduino, run the command again, and note what's missing. Plug it back in and note what appeared.

Test the connection:
```bash
# Install screen if needed
sudo apt-get install screen

# Connect to your Arduino (replace ttyACM0 with your port)
screen /dev/ttyACM0 9600

# You should see temperature readings streaming in like:
# MEASURE:1:23.5
# MEASURE:1:23.4
# MEASURE:1:23.6

# Exit screen: Press Ctrl+A then Ctrl+D
```

---

### Step 6: Start the Hardware Bridge

**What this does:** Launches the daemon that reads measurements from the Arduino and sends commands back to it. This is the communication middleman between Arduino and API.

**How to do it:** Open a new terminal and run:

```bash
python -m app.hardware.serial_bridge \
  --port /dev/ttyACM0 \
  --baudrate 9600 \
  --api-url http://localhost:8000 \
  --poll-interval 2.0
```

**Parameter explanations:**
- `--port /dev/ttyACM0`: Serial port your Arduino is connected to (from Step 5)
- `--baudrate 9600`: Must match your Arduino code (line 11 in the example above)
- `--api-url http://localhost:8000`: Where the API server is running
- `--poll-interval 2.0`: Check for pending commands every 2 seconds

**Expected output (should show continuous logging):**
```
2026-06-02 22:00:01 - INFO - app.hardware.serial_bridge - Connected to /dev/ttyACM0 at 9600 baud
2026-06-02 22:00:05 - INFO - app.hardware.serial_bridge - Received from Arduino: MEASURE:1:23.5
2026-06-02 22:00:05 - INFO - app.hardware.serial_bridge - Stored measurement: temperature_sensor_1=23.5
```

**If it fails to connect:**
- Check the port: `ls /dev/tty*` — Make sure your port exists
- Check the baudrate: Should match Arduino code exactly
- Check USB cable: Make sure it's firmly connected
- Check Arduino IDE: Make sure code was uploaded successfully

Leave this terminal open—the bridge must run continuously.

---

### Step 7: Verify Measurements Are Being Stored

**What this does:** Confirms that measurements from the Arduino are successfully reaching the API database.

**How to do it:** In a new terminal, query the measurements endpoint:

```bash
# Get recent measurements
curl http://localhost:8000/measurements?limit=10
```

**Expected response (if everything works):**
```json
{
  "status": "ok",
  "message": "got measurements",
  "data": [
    {
      "id": 1,
      "source": "arduino",
      "name": "temperature_sensor_1",
      "value": 23.5,
      "unit": null,
      "timestamp": "2026-06-02T22:00:05.123456+00:00"
    },
    {
      "id": 2,
      "source": "arduino",
      "name": "temperature_sensor_1",
      "value": 23.4,
      "unit": null,
      "timestamp": "2026-06-02T22:00:10.123456+00:00"
    }
  ]
}
```

If you see measurements appearing and updating, **success!** The measurement pipeline works.

---

### Step 8: Create an Automation Rule (Optional but Recommended)

**What this does:** Creates a rule that automatically triggers when sensor conditions are met. This demonstrates the full end-to-end system.

**Example:** "If temperature exceeds 25°C, turn on the LED"

**How to do it:**
```bash
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "temperature_warning",
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

**Field explanations:**
- `name`: Unique name for this rule
- `enabled`: Set to `true` to activate; `false` to disable
- `condition_measurement`: Name of the sensor being monitored (from Step 2)
- `condition_operator`: One of: `">"`, `"<"`, `">="`, `"<="`, `"=="`
- `condition_value`: The threshold value
- `action_sensor`: Name of the sensor to control (from Step 2)
- `action_state`: The state to set it to (`"ON"` or `"OFF"`)

**Expected response:**
```json
{
  "status": "ok",
  "message": "rule created",
  "data": {"id": 1}
}
```

**What happens now:**
1. Arduino reads temperature (Step 4 code running)
2. Hardware bridge sends measurement to API (Step 6 running)
3. API evaluates rule automatically
4. When temperature > 25°C, API creates a command: "Turn ON led_1"
5. Hardware bridge polls for pending commands (every 2 seconds)
6. Hardware bridge sends command to Arduino: `COMMAND:2:ON`
7. Arduino receives command and executes it: LED turns on physically

**Test it:** Heat up the temperature sensor (hold it or breathe on it) and watch the LED turn on!

---

### Step 9: Verify the Full Pipeline Works

**What this does:** Confirms that measurements trigger rules and commands are executed.

**How to do it:**

1. Check pending commands:
```bash
curl http://localhost:8000/commands/pending
```

If there are any pending commands, the hardware bridge will send them to Arduino. If response is empty (`"data": []`), no commands are pending yet.

2. Check all commands (including executed ones):
```bash
curl http://localhost:8000/commands
```

3. Physically test: Change your sensor input (temperature, light, etc.) and watch:
   - Measurements appear in `/measurements` endpoint
   - Rules evaluate and create commands
   - Hardware bridge logs show "Sent command"
   - Physical actuator (LED) responds

If all of this happens, the system is fully integrated!

---

## Serial Protocol Reference

The system uses a simple text-based protocol for communication. All messages are terminated with a newline character (`\n`).

### Format: Arduino Sends Measurements to Server

**Protocol:** `MEASURE:sensor_id:value`

**What it means:**
- `MEASURE` = This is a measurement (not a command)
- `sensor_id` = The ID of the sensor sending this (from Step 2)
- `value` = The numeric reading (can be integer or decimal)

**Examples:**
```
MEASURE:1:23.5
MEASURE:1:24.2
MEASURE:2:1023
```

Each line represents one sensor reading. The hardware bridge parses this and converts it to a proper measurement in the database.

### Format: Server Sends Commands to Arduino

**Protocol:** `COMMAND:sensor_id:action`

**What it means:**
- `COMMAND` = This is an instruction to execute
- `sensor_id` = Which sensor/actuator to control
- `action` = What to do (typically `ON` or `OFF`, but can be any string)

**Examples:**
```
COMMAND:2:ON
COMMAND:2:OFF
COMMAND:3:100
```

The Arduino receives these messages and executes the corresponding pin operations.

---

## Troubleshooting

### Problem: Hardware bridge fails to start or can't connect

**Symptoms:** Error message like `Error connecting to /dev/ttyACM0` or `No such file or directory`

**Solutions:**
1. Verify the port exists:
   ```bash
   ls /dev/tty*
   ```
   Your Arduino should appear as `/dev/ttyUSB0`, `/dev/ttyACM0`, or similar.

2. Check USB connection:
   - Unplug Arduino, run `ls /dev/tty*`, note what's gone
   - Plug in Arduino, run again, see what appeared
   - Use that port in the hardware bridge command

3. Try different baud rates:
   - Common values: 9600, 115200
   - Must match your Arduino code (line 11 in example)

4. Check permissions (if you get "Permission denied"):
   ```bash
   # Add your user to dialout group (one-time setup)
   sudo usermod -a -G dialout $USER
   # Then log out and log back in
   ```

### Problem: No measurements appearing in the API

**Symptoms:** The hardware bridge is running but measurements aren't reaching the API

**Solutions:**
1. Verify Arduino is sending data:
   ```bash
   screen /dev/ttyACM0 9600
   # Watch for MEASURE messages
   # Exit: Ctrl+A then Ctrl+D
   ```

2. Check hardware bridge logs for errors:
   - Look for "Received from Arduino:" messages
   - Look for "Failed to parse" or "Error handling measurement"

3. Verify sensor IDs match:
   - Arduino code uses `SENSOR_ID_TEMP=1` (line 5 in example)
   - This must match the sensor ID from Step 2
   - If mismatched, the API won't recognize the measurement

4. Confirm API is running:
   ```bash
   curl http://localhost:8000/sensors
   ```
   Should return a list of sensors

### Problem: Commands not reaching the Arduino

**Symptoms:** You create a rule, it triggers, but the Arduino doesn't respond

**Solutions:**
1. Check if commands are being created:
   ```bash
   curl http://localhost:8000/commands
   ```
   You should see recent commands with status "acknowledged"

2. Check hardware bridge is polling:
   - Hardware bridge should log "polling for commands" every 2 seconds
   - Check the `--poll-interval` setting (should be 2.0 or lower)

3. Verify the command format:
   ```bash
   # Manually create a test command
   curl -X POST http://localhost:8000/commands \
     -H "Content-Type: application/json" \
     -d '{"sensor_id": 2, "action": "ON"}'
   ```
   Watch the hardware bridge logs to see if it sends the command

4. Check Arduino serial monitor:
   - In Arduino IDE, open Tools → Serial Monitor
   - Set baud rate to match your code (9600 in example)
   - You should see incoming `COMMAND:` messages

### Problem: API says LED is ON but it's actually OFF

**Symptoms:** State mismatch between API and physical hardware

**Solutions:**
1. The issue is usually command delivery
   - Check if the command actually reached the Arduino (serial monitor)
   - Check if Arduino code correctly handles the pin

2. Verify pin configuration:
   - Arduino code: `#define LED_PIN 5` (example)
   - Actual physical LED: Connected to pin 5?
   - Try a test with: `digitalWrite(LED_PIN, HIGH)`

3. Check for Arduino resets:
   - Arduino may have crashed or reset
   - Check for Serial errors in Arduino logs
   - Try a manual command and watch serial output

---

## Testing Without Physical Hardware

**Scenario:** You want to test the system before connecting real Arduino

**How to do it:**

```bash
# Terminal 1: Start the API
uvicorn app.main:app

# Terminal 2: Start hardware bridge in test mode (uses stdin)
python -m app.hardware.serial_bridge

# Terminal 3: Send test measurements manually
# Type this and press Enter:
# MEASURE:1:23.5
# Then type:
# MEASURE:1:24.0

# Terminal 4: In another terminal, trigger a rule and watch for commands
curl http://localhost:8000/commands/pending
```

The hardware bridge will display commands it would send to a real Arduino.

---

## API Endpoint Reference

### Sensors (Create and view logical sensor entities)

- `POST /sensors` — Create a new sensor
- `GET /sensors` — List all sensors
- `GET /sensors/{name}` — Get specific sensor
- `POST /sensors/{name}/state` — Update sensor state

### Hardware Configuration (Map sensors to Arduino pins)

- `POST /hardware` — Register a pin mapping
- `GET /hardware` — List all pin mappings
- `GET /hardware/{sensor_id}` — Get mapping for specific sensor

### Commands (Queue up and track instructions)

- `POST /commands` — Create a command (usually done automatically by rules)
- `GET /commands/pending` — Get pending commands (called by hardware bridge every 2 seconds)
- `POST /commands/{command_id}/ack` — Mark command as executed (called by hardware bridge)
- `GET /commands` — List all commands (including history)

### Measurements (Incoming sensor data)

- `POST /measurements` — Submit a measurement (called by hardware bridge)
- `GET /measurements` — List measurements
- `GET /measurements?name=sensor_name` — Filter by sensor name

### Rules (Automation logic)

- `POST /rules` — Create a rule
- `GET /rules` — List rules
- `POST /rules/{name}/enabled` — Enable/disable a rule

---

## Common Sensor Configurations

### Temperature Sensor (Analog)

```bash
# Create sensor
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "temperature", "state": "OFF"}'

# Arduino code: analogRead(A0) on pin A0
# Hardware config:
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 1,
    "arduino_pin": "A0",
    "pin_type": "analog",
    "read_interval_ms": 5000
  }'
```

### LED (Digital Output)

```bash
# Create sensor
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "led", "state": "OFF"}'

# Arduino code: digitalWrite(5, HIGH/LOW)
# Hardware config:
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 2,
    "arduino_pin": "D5",
    "pin_type": "digital",
    "read_interval_ms": 1000
  }'
```

### Motion Sensor (Digital Input)

```bash
# Create sensor
curl -X POST http://localhost:8000/sensors \
  -H "Content-Type: application/json" \
  -d '{"name": "motion", "state": "OFF"}'

# Arduino code: digitalRead(2) on pin D2
# Hardware config:
curl -X POST http://localhost:8000/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": 3,
    "arduino_pin": "D2",
    "pin_type": "digital",
    "read_interval_ms": 1000
  }'
```

---

## Performance Tuning

- **Hardware bridge poll interval:** Lower = faster command response, but more API requests. Default 2 seconds is reasonable.
- **Arduino read interval:** Lower = more frequent measurements, but uses more serial bandwidth and CPU. 5 seconds for temperature is typical.
- **Serial baud rate:** Higher = faster communication (115200 is fast but requires reliable connection). 9600 is safe for most setups.
- **Number of sensors:** Each sensor adds one line per read interval. With 10 sensors at 5 second intervals, that's 2 messages per second—well within serial capacity.

---

## Architecture Deep Dive

### Why separate Hardware Bridge from API?

The hardware bridge runs as an independent daemon because:

1. **Continuity:** If the API restarts, measurements keep flowing (bridge buffers, retries)
2. **Isolation:** Hardware issues don't crash the API
3. **Simplicity:** The API doesn't need to manage serial ports directly
4. **Flexibility:** You can run the bridge on a different machine if needed
5. **Testability:** You can test the API without hardware connected

### The Rule → Command → Execution Flow

```
1. Measurement arrives: POST /measurements
2. Rule engine evaluates all enabled rules
3. When rule condition matches:
   - Insert row into commands table: INSERT INTO commands (sensor_id, action, status=PENDING)
4. Hardware bridge polls: GET /commands/pending
5. Bridge sends to Arduino: COMMAND:sensor_id:action
6. Arduino executes action (digitalWrite, etc.)
7. Bridge acknowledges: POST /commands/{id}/ack
8. Command status changes: PENDING → ACKNOWLEDGED
```

### Why Commands Table?

The `commands` table serves as a queue and audit log:

- **Queue:** Pending commands wait until bridge polls them
- **Tracking:** You can see what commands were issued and when
- **Retry:** Commands remain pending if bridge crashes (automatic retry when it restarts)
- **Audit:** History of all commands provides debugging and logging
- **Acknowledgment:** Confirms the bridge actually sent each command

---

## Next Steps

1. **Set up your first sensor:** Pick one sensor type (temperature, LED, motion)
2. **Test end-to-end:** Follow Steps 1-7 above, verify measurements flow
3. **Add more sensors:** Once one works, adding more is straightforward
4. **Create rules:** Set up automation based on real sensor data
5. **Monitor and log:** Use API endpoints to track system behavior
6. **Optimize:** Adjust read intervals and poll intervals based on your needs
