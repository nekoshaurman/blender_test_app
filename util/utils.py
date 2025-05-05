import os
import shutil
import subprocess
import logging
from logging.handlers import RotatingFileHandler

from managers.config_manager import config_manager

# Configure logging
logger = logging.getLogger('BlenderUtils')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler('blender_interface.log', maxBytes=1048576, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def transform_path_to_standard(path: str) -> str:
    """Convert path to standard format by replacing forward slashes with backslashes."""
    if not isinstance(path, str):
        logger.error(f"Invalid path type: {type(path)}, expected string")
        raise TypeError("Path must be a string")
    if not path:
        logger.warning("Empty path provided")
        return ""
    try:
        standardized_path = path.replace('/', '\\')
        logger.debug(f"Transformed path: {path} -> {standardized_path}")
        return standardized_path
    except Exception as e:
        logger.error(f"Error transforming path {path}: {str(e)}")
        raise


def path_to_thumbnail(project_name_in_queue: str) -> str:
    """Generate path to thumbnail for a given project."""
    if not isinstance(project_name_in_queue, str):
        logger.error(f"Invalid project name type: {type(project_name_in_queue)}, expected string")
        raise TypeError("Project name must be a string")
    if not project_name_in_queue:
        logger.warning("Empty project name provided")
        return ""

    try:
        work_directory = config_manager.get_variable("work_directory")
        if not work_directory:
            logger.error("Work directory not set in config")
            raise ValueError("Work directory is not configured")

        thumbnail_path = f"{work_directory}\\thumbnails\\{project_name_in_queue}.png"
        logger.debug(f"Generated thumbnail path: {thumbnail_path}")
        return thumbnail_path
    except Exception as e:
        logger.error(f"Error generating thumbnail path for {project_name_in_queue}: {str(e)}")
        raise


def set_config_value(key: str, value) -> None:
    """Set a configuration value in the config manager."""
    if not isinstance(key, str):
        logger.error(f"Invalid key type: {type(key)}, expected string")
        raise TypeError("Key must be a string")
    if not key:
        logger.error("Empty key provided")
        raise ValueError("Key cannot be empty")

    try:
        config_manager.set_variable(key, value)
        logger.info(f"Set config value: {key} = {value}")
    except Exception as e:
        logger.error(f"Error setting config value {key}: {str(e)}")
        raise


def get_config_value(key: str):
    """Get a configuration value from the config manager."""
    if not isinstance(key, str):
        logger.error(f"Invalid key type: {type(key)}, expected string")
        raise TypeError("Key must be a string")
    if not key:
        logger.error("Empty key provided")
        raise ValueError("Key cannot be empty")

    try:
        value = config_manager.get_variable(key)
        logger.debug(f"Retrieved config value: {key} = {value}")
        return value
    except Exception as e:
        logger.error(f"Error getting config value {key}: {str(e)}")
        raise


def get_file_name_from_path(file_path: str) -> str:
    """Extract the file name from a file path."""
    if not isinstance(file_path, str):
        logger.error(f"Invalid file path type: {type(file_path)}, expected string")
        raise TypeError("File path must be a string")
    if not file_path:
        logger.warning("Empty file path provided")
        return ""

    try:
        file_name = os.path.basename(file_path)
        logger.debug(f"Extracted file name: {file_path} -> {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"Error extracting file name from {file_path}: {str(e)}")
        raise


def is_path_exists(file_path: str) -> bool:
    """Check if a file or directory path exists."""
    if not isinstance(file_path, str):
        logger.error(f"Invalid file path type: {type(file_path)}, expected string")
        raise TypeError("File path must be a string")
    if not file_path:
        logger.warning("Empty file path provided")
        return False

    try:
        exists = os.path.exists(file_path)
        logger.debug(f"Path {file_path} exists: {exists}")
        return exists
    except Exception as e:
        logger.error(f"Error checking if path {file_path} exists: {str(e)}")
        return False


def get_cpu_count() -> int:
    """Get the number of CPU cores available."""
    try:
        cpu_count = os.cpu_count()
        if cpu_count is None:
            logger.warning("Unable to determine CPU count")
            return 1  # Fallback to 1 if undetermined
        logger.debug(f"CPU count: {cpu_count}")
        return cpu_count
    except Exception as e:
        logger.error(f"Error getting CPU count: {str(e)}")
        return 1  # Fallback to 1 on error


def set_blender_in_path(blender_path: str) -> None:
    """Add Blender path to the system PATH environment variable."""
    if not isinstance(blender_path, str):
        logger.error(f"Invalid blender path type: {type(blender_path)}, expected string")
        raise TypeError("Blender path must be a string")
    if not blender_path:
        logger.error("Empty blender path provided")
        raise ValueError("Blender path cannot be empty")

    try:
        # Remove \blender.exe if present
        clean_path = blender_path
        if blender_path.lower().endswith("\\blender.exe"):
            clean_path = blender_path[:-12]  # Remove last 12 characters ("\blender.exe")

        if not os.path.exists(clean_path):
            logger.error(f"Blender path does not exist: {clean_path}")
            raise ValueError(f"Blender path does not exist: {clean_path}")

        # Add cleaned path to PATH
        os.environ["PATH"] = clean_path + os.pathsep + os.environ["PATH"]
        logger.info(f"Added Blender path to PATH: {clean_path}")
    except Exception as e:
        logger.error(f"Error setting Blender path {blender_path}: {str(e)}")
        raise


def is_blender_bin(blender_path: str) -> bool:
    """Check if the provided path is a valid Blender executable."""
    if not isinstance(blender_path, str):
        logger.error(f"Invalid blender path type: {type(blender_path)}, expected string")
        raise TypeError("Blender path must be a string")
    if not blender_path:
        logger.error("Empty blender path provided")
        return False

    try:
        # Check if file exists
        if not os.path.exists(blender_path):
            logger.warning(f"Blender path does not exist: {blender_path}")
            return False

        # Run Blender version check with timeout
        result = subprocess.run(
            [blender_path, '--version'],
            capture_output=True,
            text=True,
            timeout=1
        )

        # Check if output contains 'Blender'
        if result.returncode == 0 and 'Blender' in result.stdout:
            logger.info(f"Valid Blender executable: {blender_path}")
            return True
        else:
            logger.warning(f"Invalid Blender executable: {blender_path}")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to validate Blender executable {blender_path}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating Blender executable {blender_path}: {str(e)}")
        return False


def get_blender_paths() -> dict:
    """Retrieve a dictionary of valid Blender executable paths and their versions."""
    blender_paths = {}

    try:
        # Get paths from config
        config_paths = config_manager.get_variable("bin_paths")
        if config_paths is not None:
            if not isinstance(config_paths, dict):
                logger.error(f"Invalid config_paths type: {type(config_paths)}, expected dict")
                raise TypeError("Config paths must be a dictionary")

            for blender_path, blender_version in config_paths.items():
                if not isinstance(blender_path, str):
                    logger.warning(f"Skipping invalid path type in config: {type(blender_path)}")
                    continue
                if not isinstance(blender_version, str):
                    logger.warning(f"Skipping invalid version type for {blender_path}: {type(blender_version)}")
                    continue
                if is_path_exists(blender_path) and is_blender_bin(blender_path):
                    blender_paths[blender_path] = blender_version
                    logger.debug(f"Added config Blender path: {blender_path} (version: {blender_version})")

        # Get path from PATH environment variable
        blender_path_from_environment = shutil.which("blender")
        if blender_path_from_environment:
            blender_path_from_environment = blender_path_from_environment.replace(".EXE", ".exe")
            if not isinstance(blender_path_from_environment, str):
                logger.warning(f"Invalid environment path type: {type(blender_path_from_environment)}")
            elif blender_path_from_environment not in blender_paths:
                if is_blender_bin(blender_path_from_environment):
                    blender_paths[blender_path_from_environment] = get_blender_version(blender_path_from_environment)
                    logger.debug(f"Added environment Blender path: {blender_path_from_environment}")

        logger.info(f"Retrieved {len(blender_paths)} Blender paths")
        return blender_paths
    except Exception as e:
        logger.error(f"Error retrieving Blender paths: {str(e)}")
        raise


def get_blender_version(blender_bin_path: str) -> str:
    """Retrieve the version of a Blender executable."""
    if not isinstance(blender_bin_path, str):
        logger.error(f"Invalid blender bin path type: {type(blender_bin_path)}, expected string")
        raise TypeError("Blender bin path must be a string")
    if not blender_bin_path:
        logger.error("Empty blender bin path provided")
        return "Invalid path"

    try:
        if not os.path.exists(blender_bin_path):
            logger.warning(f"Blender bin path does not exist: {blender_bin_path}")
            return "Path does not exist"

        result = subprocess.run(
            [blender_bin_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Search for version in output
        for line in (result.stdout + result.stderr).splitlines():
            if line.startswith('Blender'):
                logger.debug(f"Blender version for {blender_bin_path}: {line.strip()}")
                return line.strip()

        logger.warning(f"No Blender version found for {blender_bin_path}")
        return "Version not found"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"Error getting Blender version for {blender_bin_path}: {str(e)}")
        return f"Error: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error getting Blender version for {blender_bin_path}: {str(e)}")
        return f"Error: {str(e)}"