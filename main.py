import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui

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


def apply_stylesheet(app):
    # Load and apply stylesheet
    try:
        with open('./gui/styles/blender_style.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        logger.warning("style.qss not found, using default styling")
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {str(e)}")


if __name__ == "__main__":
    try:
        work_directory = os.path.dirname(os.path.abspath(__file__))
        utils.set_config_value("work_directory", work_directory)
        logger.info(f"Set working directory: {work_directory}")

        app = QApplication(sys.argv + ['-platform', 'windows:darkmode=1'])

        apply_stylesheet(app)
        app.setStyle('Fusion')
        app.setFont(QtGui.QFont("Blender Mono I18n", 10))

        window = BlenderInterface()
        window.setFixedSize(1600, 900)
        window.show()

        logger.info("Application started")

        sys.exit(app.exec_())
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        sys.exit(1)
