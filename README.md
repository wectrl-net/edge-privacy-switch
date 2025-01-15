# Edge Privacy Switch

This project allows you to control public internet access on a Linux-based device (such as a Raspberry Pi) using an M5Stack Matrix device running ESPHome or other compatible devices. The M5Stack device will display "ON" or "OFF" on its screen, and based on this state, the Linux device will enable or disable public internet access while still allowing access to internal LAN IPs.

[![Project Demo](https://img.youtube.com/vi/Bmi3v72_KJw/0.jpg)](https://www.youtube.com/watch?v=Bmi3v72_KJw)

## Features

- Hardware privacy switch monitoring via serial connection
- Configurable network access control using iptables
- Service management (start/stop) based on privacy state
- State persistence via file system
- Bi-directional state synchronization with ESPHome device
- MQTT support for external integrations
- Automatic serial port detection
- Comprehensive logging
- YAML-based configuration

## Project Structure

- **edge-privacy-switch-agent.py**: The Python script that runs on the Linux device. It monitors the serial output from the M5Stack device and controls the network access accordingly.
- **edge-privacy-switch-agent.service**: A systemd service file to run the Python script as a background service.
- **config.yaml**: Configuration file for customizing the agent's behavior.
- **esphome-m5-matrix-privacy-switch.yaml**: The ESPHome configuration for the M5Stack Matrix device.

## Prerequisites

- **M5Stack Matrix**: A device that will display the current state ("ON" or "OFF") and communicate this state to the Linux device over serial.
- **ESPHome**: Used to flash the M5Stack device with the provided YAML configuration.
- **Linux Device**: Such as a Raspberry Pi, where the Python script will run and control network access.
- **Python Dependencies**: pyserial, pyyaml, paho-mqtt

## Setup Instructions

### Step 1: Flash M5Stack with ESPHome

1. Install ESPHome on your system.
2. Flash the M5Stack device using the provided configuration:
```bash
esphome run esphome-m5-matrix-privacy-switch.yaml
```

### Step 2: Setup the Python Agent

1. Clone the project:
```bash
git clone <project-url>
```

2. Install dependencies:
```bash
pip install pyserial pyyaml paho-mqtt
```

3. Create required directories:
```bash
sudo mkdir -p /var/lib/edge-privacy-switch
sudo chown your-user:your-group /var/lib/edge-privacy-switch
```

4. Copy files and setup service:
```bash
sudo cp -r edge-privacy-switch /opt/
cd /opt/edge-privacy-switch/ && ./setup.sh && cd -
```

## Configuration

The agent uses a YAML configuration file for customization. The default configuration will be created at first run:

```yaml
# Serial Communication Settings
serial:
  baud_rate: 115200
  port: ""          # Leave empty for auto-detection

# State file settings
state:
  file_path: "/var/lib/edge-privacy-switch/state"

# MQTT Settings
mqtt:
  enabled: true
  broker: "localhost"
  port: 1883
  username: ""
  password: ""
  topic: "privacy_switch/state"
  client_id: "edge-privacy-switch"

# Actions
actions:
  iptables:
    enabled: true
    internal_subnets:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
    chains:
      - 'INPUT'
      - 'OUTPUT'
      - 'FORWARD'

  commands:
    privacy_on:
      - command: "systemctl stop nginx"
        enabled: false
    privacy_off:
      - command: "systemctl start nginx"
        enabled: false
```

### Running the Service

Start the service:
```bash
sudo systemctl start edge-privacy-switch-agent
```

Enable at boot:
```bash
sudo systemctl enable edge-privacy-switch-agent
```

Check status:
```bash
sudo systemctl status edge-privacy-switch-agent
```

### Command Line Options

The agent accepts one optional argument:
```bash
python3 edge-privacy-switch-agent.py --config /path/to/config.yaml
```

## State Management

The system maintains state in multiple ways:

1. **File System State**: 
   - JSON file with privacy state and timestamp
   - Updated on every state change
   - Default location: `/var/lib/edge-privacy-switch/state`

2. **Device Synchronization**:
   - Bi-directional communication with ESPHome device
   - Automatic state synchronization on startup
   - State change acknowledgments

3. **MQTT State** (optional):
   - Published to configured topic
   - Retained messages for persistence
   - Useful for external system integration

## Communication Protocol

The agent and ESPHome device communicate using these messages:

- `Privacy Switch: ON/OFF` - Device state change notification
- `GET_STATE` - Agent requests current state
- `STATE:ON/OFF` - Device state response
- `ACK:ON/OFF` - Agent acknowledges state change
- `Trigger Host Reboot` - Device requests system reboot

## Logging

The agent logs to:
- Console output
- `/var/log/edge-privacy-switch.log`

## Security Considerations

- The agent requires sudo privileges for iptables operations
- Custom commands run with the same privileges as the agent
- Review and test custom commands before enabling them
- Ensure proper permissions on configuration and state files
- Use MQTT authentication when exposed to untrusted networks

## Troubleshooting

- Check systemd service status for errors
- Review logs at `/var/log/edge-privacy-switch.log`
- Verify serial port permissions and connectivity
- Ensure iptables and required commands are available

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contributing

Feel free to submit issues or pull requests if you find bugs or have improvements to suggest.