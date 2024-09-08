# Edge Privacy Switch

This project allows you to control public internet access on a Linux-based device (such as a Raspberry Pi) using an M5Stack Matrix device running ESPHome or other compatible devices. The M5Stack device will display "ON" or "OFF" on its screen, and based on this state, the Linux device will enable or disable public internet access while still allowing access to internal LAN IPs.

[![Project Demo](https://img.youtube.com/vi/Bmi3v72_KJw/0.jpg)](https://www.youtube.com/watch?v=Bmi3v72_KJw)

## Project Structure

- **edge-privacy-switch-agent.py**: The Python script that runs on the Linux device. It monitors the serial output from the M5Stack device and controls the network access accordingly.
- **edge-privacy-switch-agent.service**: A systemd service file to run the Python script as a background service on the Linux device.
- **esphome-m5-matrix-privacy-switch.yaml**: The ESPHome configuration for the M5Stack Matrix device. It displays "ON" or "OFF" on the screen and sends the state over the serial port.

## Prerequisites

- **M5Stack Matrix**: A device that will display the current state ("ON" or "OFF") and communicate this state to the Linux device over serial.
- **ESPHome**: Used to flash the M5Stack device with the provided YAML configuration.
- **Linux Device**: Such as a Raspberry Pi, where the Python script will run and control network access.

## Setup Instructions

### Step 1: Flash M5Stack with ESPHome

1. Install ESPHome on your system.
2. Flash the M5Stack device using the provided `esphome-m5-matrix-privacy-switch.yaml` configuration file:
    ```bash
    esphome run esphome-m5-matrix-privacy-switch.yaml
    ```
3. The M5Stack device should now display "ON" or "OFF" and send this state over the serial connection.

### Step 2: Setup the Python Agent on the Linux Device

1. **Clone the project**:
    ```bash
    git clone <project-url>
    ```
2. **Copy the Python script to your /opt/**:
    ```bash
    cp edge-privacy-switch /opt/
    ```
3. **Go to dir and run setup script**:
    ```bash
    cd /opt/edge-privacy-switch/ && ./setup.sh && cd -
    ```

### Step 3: Verify the Setup

- Check if the Python script is running:
  ```bash
  sudo systemctl status edge-privacy-switch-agent.service
  ```
- Monitor the log file for any errors or status messages:
  ```bash
  tail -f /var/log/serial_monitor.log
  ```

### Configuration

The Python script uses environment variables and command-line arguments for configuration:

- **Environment Variables**:
  - `BAUD_RATE`: Set the baud rate for the serial connection (default: 115200).
  - `SERIAL_PORT`: Specify the serial port if auto-detection fails.

- **Command-Line Arguments**:
  - `--baud_rate`: Set the baud rate for the serial connection.
  - `--serial_port`: Specify the serial port.

Example usage:
```bash
python3 /usr/local/bin/edge-privacy-switch-agent.py --baud_rate 9600 --serial_port /dev/ttyUSB0
```

### Security Considerations

- Ensure the Python script has appropriate permissions to modify iptables rules.
- The script should be run as a privileged user or have necessary sudo privileges.

### Troubleshooting

- If the serial port cannot be detected, make sure the M5Stack device is properly connected and that the correct serial port is being used.
- Check the log file `/var/log/serial_monitor.log` for detailed error messages and debugging information.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contributions

Feel free to submit issues or pull requests if you find bugs or have improvements to suggest.