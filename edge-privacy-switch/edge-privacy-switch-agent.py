import serial
import subprocess
import os
import re
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/edge-privacy-switch.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Define internal subnets typically used in private networks
INTERNAL_SUBNETS = [
    '10.0.0.0/8',
    '172.16.0.0/12',
    '192.168.0.0/16'
]

CHAINS_JOIN = [
    'INPUT', 'OUTPUT', 'FORWARD'
]

def get_default_interface():
    try:
        route_output = subprocess.check_output(['ip', 'route', 'show', 'default']).decode('utf-8')
        match = re.search(r'dev (\w+)', route_output)
        if match:
            interface = match.group(1)
            logger.info(f"Default network interface found: {interface}")
            return interface
        else:
            logger.error("No default network interface found.")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to retrieve default network interface: {e}")
        return None

def find_serial_port():
    try:
        ports = subprocess.check_output(['ls', '/dev/']).decode('utf-8').splitlines()
        usb_ports = [p for p in ports if 'ttyUSB' in p or 'ttyACM' in p]
        if usb_ports:
            serial_port = f'/dev/{usb_ports[0]}'
            logger.info(f"Serial port detected: {serial_port}")
            return serial_port
        else:
            logger.error("No serial port found.")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list /dev/ devices: {e}")
        return None

def set_iptables_rule(enable):
    interface = get_default_interface()
    if not interface:
        logger.error("Cannot set iptables rule without a network interface.")
        return

    try:
        if enable:
            # Remove the rules that block public IP access
            subprocess.run(['sudo', 'iptables', '-F', 'WECTRL_NETBLOCK'])
            for chain in CHAINS_JOIN:
                subprocess.run(['sudo', 'iptables', '-D', chain, '-j', 'WECTRL_NETBLOCK'])
            subprocess.run(['sudo', 'iptables', '-X', 'WECTRL_NETBLOCK'])

            logger.info("Public Internet Enabled")
        else:
            # Add the rule to block public IP access while allowing LAN IPs
            subprocess.run(['sudo', 'iptables', '-N', 'WECTRL_NETBLOCK'])

            for subnet in INTERNAL_SUBNETS:
                subprocess.run(['sudo', 'iptables', '-A', 'WECTRL_NETBLOCK', '-s', subnet, '-j', 'ACCEPT'])

            subprocess.run(['sudo', 'iptables', '-A', 'WECTRL_NETBLOCK', '-j', 'DROP'])

            for chain in CHAINS_JOIN:
                subprocess.run(['sudo', 'iptables', '-A', chain, '-j', 'WECTRL_NETBLOCK'])

            logger.info("Public Internet Disabled")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set iptables rule: {e}")

def reboot_host():
    subprocess.call(["shutdown", "-r", "-t", "now"])

def monitor_serial(serial_port, baud_rate):
    try:
        ser = serial.Serial(serial_port, baud_rate)
        logger.info(f"Serial connection established on {serial_port} at {baud_rate} baud.")
    except serial.SerialException as e:
        logger.error(f"Failed to open serial port {serial_port}: {e}")
        return

    current_state = None

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            logger.debug(f"Serial line received: {line}")
            if 'Privacy Switch: ON' in line and current_state != 'ON':
                logger.info("Received: Privacy Switch: ON")
                set_iptables_rule(enable=False)
                current_state = 'ON'
            if 'Privacy Switch: OFF' in line and current_state != 'OFF':
                logger.info("Received: Privacy Switch: OFF")
                set_iptables_rule(enable=True)
                current_state = 'OFF'
            elif 'Trigger Host Reboot' in line:
                logger.info("Got a Host reboot command! Rebooting System...")
                reboot_host()
        except serial.SerialException as e:
            logger.error(f"Error reading from serial port: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    # Use argparse for command-line parameters
    parser = argparse.ArgumentParser(description="Monitor serial port and control internet access based on state.")
    parser.add_argument('--baud_rate', type=int, default=int(os.getenv('BAUD_RATE', 115200)), help="Baud rate for the serial connection")
    parser.add_argument('--serial_port', type=str, default=os.getenv('SERIAL_PORT', find_serial_port()), help="Serial port to use")
    
    args = parser.parse_args()

    if not args.serial_port:
        logger.error("No serial port found or specified.")
        exit(1)

    try:
        monitor_serial(args.serial_port, args.baud_rate)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        exit(1)