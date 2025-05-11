import json
import os
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logger = logging.getLogger('ConfigManager')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler('blender_interface.log', maxBytes=1048576, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

class ConfigManager:
    def __init__(self, file_path: str = "config.json"):
        """Initialize ConfigManager with a specified config file path."""
        if not isinstance(file_path, str):
            raise TypeError(f"File path must be a string, got {type(file_path)}")
        if not file_path:
            raise ValueError("File path cannot be empty")

        self.file_path = file_path

        logger.info(f"Initializing ConfigManager with file: {self.file_path}")
        try:
            self._variables = self._load_config()
        except Exception as e:
            logger.error(f"Failed to initialize ConfigManager: {str(e)}")
            raise

    def _load_config(self) -> dict:
        """Load configuration from the JSON file."""
        logger.debug(f"Loading config from {self.file_path}")
        try:
            if not os.path.exists(self.file_path):
                logger.warning(f"Config file {self.file_path} does not exist, returning empty config")
                return {}

            with open(self.file_path, "r", encoding='utf-8') as f:
                config = json.load(f)
                if not isinstance(config, dict):
                    logger.error(f"Config file {self.file_path} contains invalid JSON, expected a dictionary")
                    raise ValueError("Config file must contain a JSON object")
                logger.info(f"Successfully loaded config from {self.file_path}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self.file_path}: {str(e)}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied accessing config file {self.file_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading config file {self.file_path}: {str(e)}")
            raise

    def _save_config(self) -> None:
        """Save the current configuration to the JSON file."""
        logger.debug(f"Saving config to {self.file_path}")
        try:
            # Ensure the directory exists if file_path includes a directory
            config_dir = os.path.dirname(self.file_path)
            if config_dir:  # Only create directory if there is a directory path
                logger.debug(f"Ensuring directory exists: {config_dir}")
                os.makedirs(config_dir, exist_ok=True)
            else:
                logger.debug(f"No directory specified for {self.file_path}, saving to current working directory: {os.getcwd()}")

            with open(self.file_path, "w", encoding='utf-8') as f:
                json.dump(self._variables, f, indent=4)
            logger.info(f"Successfully saved config to {self.file_path}")
        except PermissionError as e:
            logger.error(f"Permission denied saving config file {self.file_path}: {str(e)}")
            raise
        except FileNotFoundError as e:
            logger.error(f"Cannot save config file {self.file_path}, invalid path: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error saving config file {self.file_path}: {str(e)}")
            raise

    def set_variable(self, key: str, value) -> None:
        """Set a configuration variable and save to file."""
        if not isinstance(key, str):
            logger.error(f"Invalid key type: {type(key)}, expected string")
            raise TypeError("Key must be a string")
        if not key:
            logger.error("Empty key provided")
            raise ValueError("Key cannot be empty")

        try:
            self._variables[key] = value
            logger.info(f"Set variable '{key}' to: {value}")
            self._save_config()
        except Exception as e:
            logger.error(f"Error setting variable '{key}': {str(e)}")
            raise

    def get_variable(self, key: str):
        """Get a configuration variable."""
        if not isinstance(key, str):
            logger.error(f"Invalid key type: {type(key)}, expected string")
            raise TypeError("Key must be a string")
        if not key:
            logger.error("Empty key provided")
            raise ValueError("Key cannot be empty")

        try:
            value = self._variables.get(key)
            logger.debug(f"Retrieved variable '{key}': {value}")
            return value
        except Exception as e:
            logger.error(f"Error getting variable '{key}': {str(e)}")
            raise

    def has_variable(self, key: str) -> bool:
        """Check if a configuration variable exists."""
        if not isinstance(key, str):
            logger.error(f"Invalid key type: {type(key)}, expected string")
            raise TypeError("Key must be a string")
        if not key:
            logger.error("Empty key provided")
            raise ValueError("Key cannot be empty")

        try:
            exists = key in self._variables
            logger.debug(f"Checked variable '{key}' existence: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking variable '{key}' existence: {str(e)}")
            raise


# Create a singleton instance of ConfigManager
config_manager = ConfigManager()