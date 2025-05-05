import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from PyQt5.QtWidgets import QApplication

import util.utils as utils
from gui.main_gui import BlenderInterface

# Configure logging
logger = logging.getLogger('BlenderMain')
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

if __name__ == "__main__":
    try:
        work_directory = os.path.dirname(os.path.abspath(__file__))
        utils.set_config_value("work_directory", work_directory)
        logger.info(f"Set working directory: {work_directory}")

        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        window = BlenderInterface()
        window.setFixedSize(1600, 900)
        window.show()
        logger.info("Application started")
        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        sys.exit(1)