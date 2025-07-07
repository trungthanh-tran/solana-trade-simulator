import configparser
import os

def load_config(config_path="config/config.ini"):
    """Load configuration from config.properties file."""
    config = configparser.ConfigParser()
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    config.read(config_path)
    return config

# Load config at module level
config = load_config()
print(f"{config['Telegram']['api_token']}")
DB_FILE = config['Database']['db_file']
TELEGRAM_API_TOKEN = config['Telegram']['api_token']