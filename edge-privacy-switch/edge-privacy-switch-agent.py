import serial
import subprocess
import os
import re
import argparse
import logging
import yaml
from pathlib import Path

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

def load_or_create_config(config_path=None):
    if config_path:
        config_path = Path(config_path)
    else:
        config_path = Path(__file__).parent / 'config.yaml'
    
    # Default configuration
    default_config = {
        'serial': {
            'baud_rate': 115200,
            'port': ''
        },
        'actions': {
            'iptables': {
                'enabled': True,
                'internal_subnets': [
                    '10.0.0.0/8',
                    '172.16.0.0/12',
                    '192.168.0.0/16'
                ],
                'chains': ['INPUT', 'OUTPUT', 'FORWARD']
            },
            'commands': {
                'privacy_on': [
                    {'command': 'systemctl stop nginx', 'enabled': False},
                    {'command': 'systemctl stop docker', 'enabled': False}
                ],
                'privacy_off': [
                    {'command': 'systemctl start nginx', 'enabled': False},
                    {'command': 'systemctl start docker', 'enabled': False}
                ]
            }
        }
    }

    try:
        if not config_path.exists():
            with open(config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default configuration file at {config_path}")
            return default_config
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
    except Exception as e:
        logger.error(f"Error handling configuration file: {e}")
        return default_config

def execute_commands(commands):
    for cmd_config in commands:
        if cmd_config.get('enabled', False):
            try:
                cmd = cmd_config['command']
                subprocess.run(cmd.split(), check=True)
                logger.info(f"Successfully executed command: {cmd}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to execute command '{cmd}': {e}")

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

def set_iptables_rule(enable, config):
    if not config['actions']['iptables']['enabled']:
        logger.info("IPTables rules are disabled in configuration")
        return

    interface = get_default_interface()
    if not interface:
        logger.error("Cannot set iptables rule without a network interface.")
        return

    try:
        if enable:
            # Remove the rules that block public IP access
            subprocess.run(['sudo', 'iptables', '-F', 'WECTRL_NETBLOCK'])
            for chain in config['actions']['iptables']['chains']:
                subprocess.run(['sudo', 'iptables', '-D', chain, '-j', 'WECTRL_NETBLOCK'])
            subprocess.run(['sudo', 'iptables', '-X', 'WECTRL_NETBLOCK'])
            
            # Execute privacy_off commands
            execute_commands(config['actions']['commands']['privacy_off'])
            logger.info("Public Internet Enabled")
        else:
            # Add the rule to block public IP access while allowing LAN IPs
            subprocess.run(['sudo', 'iptables', '-N', 'WECTRL_NETBLOCK'])

            for subnet in config['actions']['iptables']['internal_subnets']:
                subprocess.run(['sudo', 'iptables', '-A', 'WECTRL_NETBLOCK', '-s', subnet, '-j', 'ACCEPT'])

            subprocess.run(['sudo', 'iptables', '-A', 'WECTRL_NETBLOCK', '-j', 'DROP'])

            for chain in config['actions']['iptables']['chains']:
                subprocess.run(['sudo', 'iptables', '-A', chain, '-j', 'WECTRL_NETBLOCK'])
            
            # Execute privacy_on commands
            execute_commands(config['actions']['commands']['privacy_on'])
            logger.info("Public Internet Disabled")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set iptables rule: {e}")

def reboot_host():
    subprocess.call(["shutdown", "-r", "-t", "now"])

def monitor_serial(serial_port, config):
    try:
        ser = serial.Serial(serial_port, config['serial']['baud_rate'])
        logger.info(f"Serial connection established on {serial_port} at {config['serial']['baud_rate']} baud.")
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
                set_iptables_rule(enable=False, config=config)
                current_state = 'ON'
            if 'Privacy Switch: OFF' in line and current_state != 'OFF':
                logger.info("Received: Privacy Switch: OFF")
                set_iptables_rule(enable=True, config=config)
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
    parser.add_argument('--config', type=str, help="Path to configuration file (optional)")
    
    args = parser.parse_args()

    # Load configuration
    config = load_or_create_config(args.config)
    
    # Get serial port from config or auto-detect
    serial_port = config['serial']['port'] or find_serial_port()
    
    if not serial_port:
        logger.error("No serial port found or specified in config.")
        exit(1)

    try:
        monitor_serial(serial_port, config)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        exit(1)