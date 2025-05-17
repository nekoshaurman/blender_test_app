import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QSpinBox, QGroupBox, QComboBox, QCheckBox, QTextEdit, QDoubleSpinBox
)

import util.utils as utils
from managers.blender_manager import BlenderManager
from dto.project import Project

# Configure logging
logger = logging.getLogger('BlenderInterface')
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


class BlenderInterface(QWidget):
    signal = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        logger.info("Initializing BlenderInterface")

        try:
            self.blender_paths = utils.get_blender_paths()
            self.projects = {}
            self.file_settings = {}
            self.preview_paths = {}
            self.current_project = None
            self.current_bin = None

            self.signal.connect(self.update_output)
            self.blender_manager = BlenderManager(self)

            self.init_ui()
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            raise

    def init_ui(self):
        logger.debug("Setting up UI")
        try:
            self.create_left_layout()
            self.create_right_layout()
            self.create_main_layout()
            self.setLayout(self.main_layout)
            self.setWindowTitle("Blender Interface")

            # Go to main to work fine with qcombobox
            # Load and apply stylesheet
            # try:
            #     with open('./gui/styles/fixblender_style.qss', 'r') as f:
            #         self.setStyleSheet(f.read())
            # except FileNotFoundError:
            #     logger.warning("style.qss not found, using default styling")
            # except Exception as e:
            #     logger.error(f"Failed to load stylesheet: {str(e)}")

        except Exception as e:
            logger.error(f"UI initialization failed: {str(e)}")
            raise

    def create_main_layout(self):
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(self.left_layout, 1)
        self.main_layout.addLayout(self.right_layout, 2)

    def create_left_layout(self):
        logger.debug("Creating left layout")
        self.left_layout = QVBoxLayout()

        # Blender binary selection
        blender_bin_layout = QHBoxLayout()
        blender_bin_label = QLabel("Blender bin:")
        blender_bin_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        blender_bin_button_layout = QHBoxLayout()
        self.blender_bin = QComboBox()
        self.blender_bin.addItems(self.blender_paths)
        self.blender_bin.currentIndexChanged.connect(self.update_blender_bin)
        self.blender_bin.setCurrentIndex(-1)

        self.blender_bin_button = QPushButton("Add")
        self.blender_bin_button.setFixedWidth(30)
        self.blender_bin_button.clicked.connect(self.add_blender_bin)

        blender_bin_layout.addWidget(blender_bin_label, stretch=1)
        blender_bin_button_layout.addWidget(self.blender_bin, stretch=2)
        blender_bin_button_layout.addWidget(self.blender_bin_button)
        blender_bin_layout.addLayout(blender_bin_button_layout, stretch=1)

        # Blender version display
        blender_version_layout = QHBoxLayout()
        blender_version_label = QLabel("Blender Version:")
        blender_version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.blender_version_text = QLabel("")
        blender_version_layout.addWidget(blender_version_label)
        blender_version_layout.addWidget(self.blender_version_text)

        # TODO: Add stop button
        # Render start button
        start_render_layout = QHBoxLayout()
        start_render_label = QLabel("Start render:")
        start_render_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.start_render_button = QPushButton("Start")
        self.start_render_button.clicked.connect(self.start_render_queue)
        start_render_layout.addWidget(start_render_label)
        start_render_layout.addWidget(self.start_render_button)

        # Blend file selection
        blend_file_layout = QHBoxLayout()
        blend_file_label = QLabel("Add .blend file")
        blend_file_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.blend_file_button = QPushButton("Add")
        self.blend_file_button.clicked.connect(self.add_blend_file)
        blend_file_layout.addWidget(blend_file_label)
        blend_file_layout.addWidget(self.blend_file_button)

        # Settings group
        settings_group = QGroupBox("Blender settings")
        settings_layout = QVBoxLayout()
        settings_layout.addLayout(blender_bin_layout)
        settings_layout.addLayout(blender_version_layout)
        settings_layout.addLayout(start_render_layout)
        settings_layout.addLayout(blend_file_layout)
        settings_group.setLayout(settings_layout)
        settings_group.setFixedSize(800, 150)
        self.left_layout.addWidget(settings_group)

        # Blend files list
        self.blend_files_list = QListWidget()
        self.blend_files_list.setSelectionMode(QListWidget.SingleSelection)
        self.blend_files_list.itemClicked.connect(self.show_file_details)
        self.left_layout.addWidget(self.blend_files_list)

        # Progress output
        self.progress_output = QTextEdit()
        self.progress_output.setReadOnly(True)
        self.progress_output.setPlaceholderText("Logs")
        self.left_layout.addWidget(self.progress_output)

    def create_right_layout(self):
        logger.debug("Creating right layout")
        self.right_layout = QVBoxLayout()

        # Main right panel
        self.right_panel = QGroupBox("Project Settings and Preview")
        self.right_panel.setFixedWidth(520)  # Set fixed width to 520 pixels
        right_panel_layout = QVBoxLayout()

        # Preview section
        self.preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview = QLabel("Select a project to see preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setScaledContents(False)
        self.render_preview_button = QPushButton("Render Preview")
        self.render_preview_button.clicked.connect(self.update_project_preview)
        preview_layout.addWidget(self.preview)
        preview_layout.addWidget(self.render_preview_button)
        self.preview_group.setLayout(preview_layout)
        self.preview_group.setFixedSize(520, 300)
        right_panel_layout.addWidget(self.preview_group)

        # Project settings section
        settings_layout = QVBoxLayout()

        # Render type selection
        render_type_layout = QHBoxLayout()
        render_type_label = QLabel("Render type:")
        render_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.render_type = QComboBox()
        self.render_type.addItems(["Movie", "Image"])
        self.render_type.setCurrentIndex(-1)
        render_type_layout.addWidget(render_type_label)
        render_type_layout.addWidget(self.render_type)
        settings_layout.addLayout(render_type_layout)

        # Frame settings
        frame_start_layout = QHBoxLayout()
        self.frame_start_label = QLabel("Start:")
        self.frame_start_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.frame_start = QSpinBox()
        self.frame_start.setRange(0, 1048574)
        frame_start_layout.addWidget(self.frame_start_label)
        frame_start_layout.addWidget(self.frame_start)
        settings_layout.addLayout(frame_start_layout)

        frame_end_layout = QHBoxLayout()
        self.frame_end_label = QLabel("End:")
        self.frame_end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.frame_end = QSpinBox()
        self.frame_end.setRange(0, 1048574)
        frame_end_layout.addWidget(self.frame_end_label)
        frame_end_layout.addWidget(self.frame_end)
        settings_layout.addLayout(frame_end_layout)

        frame_step_layout = QHBoxLayout()
        self.frame_step_label = QLabel("Step:")
        self.frame_step_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.frame_step = QSpinBox()
        self.frame_step.setRange(1, 1048574)
        frame_step_layout.addWidget(self.frame_step_label)
        frame_step_layout.addWidget(self.frame_step)
        settings_layout.addLayout(frame_step_layout)

        frame_current_layout = QHBoxLayout()
        self.frame_current_label = QLabel("Current frame:")
        self.frame_current_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.frame_current = QSpinBox()
        frame_current_layout.addWidget(self.frame_current_label)
        frame_current_layout.addWidget(self.frame_current)
        settings_layout.addLayout(frame_current_layout)

        fps_layout = QHBoxLayout()
        self.fps_value_label = QLabel("FPS:")
        self.fps_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fps_value = QSpinBox()
        self.fps_value.setRange(1, 32767)
        fps_layout.addWidget(self.fps_value_label)
        fps_layout.addWidget(self.fps_value)
        settings_layout.addLayout(fps_layout)

        fps_base_layout = QHBoxLayout()
        self.fps_base_label = QLabel("FPS Base:")
        self.fps_base_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.fps_base = QDoubleSpinBox()
        self.fps_base.setRange(1e-5, 1e6)
        self.fps_base.setSingleStep(0.1)
        fps_base_layout.addWidget(self.fps_base_label)
        fps_base_layout.addWidget(self.fps_base)
        settings_layout.addLayout(fps_base_layout)

        # Format settings
        format_group = QGroupBox("Format")
        format_layout = QVBoxLayout()
        resolution_x_layout = QHBoxLayout()
        resolution_x_label = QLabel("Resolution X:")
        resolution_x_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.resolution_x = QSpinBox()
        self.resolution_x.setRange(4, 65536)
        resolution_x_layout.addWidget(resolution_x_label)
        resolution_x_layout.addWidget(self.resolution_x)

        resolution_y_layout = QHBoxLayout()
        resolution_y_label = QLabel("Y:")
        resolution_y_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.resolution_y = QSpinBox()
        self.resolution_y.setRange(4, 65536)
        resolution_y_layout.addWidget(resolution_y_label)
        resolution_y_layout.addWidget(self.resolution_y)

        resolution_scale_layout = QHBoxLayout()
        resolution_scale_label = QLabel("%:")
        resolution_scale_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.resolution_scale = QSpinBox()
        self.resolution_scale.setRange(1, 32767)
        resolution_scale_layout.addWidget(resolution_scale_label)
        resolution_scale_layout.addWidget(self.resolution_scale)

        format_layout.addLayout(resolution_x_layout)
        format_layout.addLayout(resolution_y_layout)
        format_layout.addLayout(resolution_scale_layout)
        format_group.setLayout(format_layout)
        settings_layout.addWidget(format_group)

        # TODO: Add name of file to output

        # Output settings
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        output_format_layout = QHBoxLayout()
        output_format_label = QLabel("Output format:")
        output_format_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.output_format_combobox = QComboBox()
        output_format_layout.addWidget(output_format_label)
        output_format_layout.addWidget(self.output_format_combobox)

        output_folder_layout = QHBoxLayout()
        output_folder_label = QLabel("Output folder:")
        output_folder_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        input_button_layout = QHBoxLayout()
        self.output_folder = QLineEdit()
        self.output_folder.setReadOnly(True)
        self.output_folder_button = QPushButton("...")
        self.output_folder_button.setFixedWidth(30)
        output_folder_layout.addWidget(output_folder_label, stretch=1)
        input_button_layout.addWidget(self.output_folder, stretch=2)
        input_button_layout.addWidget(self.output_folder_button)
        output_folder_layout.addLayout(input_button_layout, stretch=1)
        output_layout.addLayout(output_format_layout)
        output_layout.addLayout(output_folder_layout)
        output_group.setLayout(output_layout)
        settings_layout.addWidget(output_group)

        # Render engine selection
        render_engine_layout = QHBoxLayout()
        render_engine_label = QLabel("Render engine:")
        render_engine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.render_engine = QComboBox()
        self.render_engine.addItems(["CYCLES", "BLENDER_EEVEE"])
        self.render_engine.setCurrentIndex(-1)
        render_engine_layout.addWidget(render_engine_label)
        render_engine_layout.addWidget(self.render_engine)
        settings_layout.addLayout(render_engine_layout)

        # Cycles settings
        self.cycles_settings = QGroupBox("Cycles settings")
        cycles_layout = QVBoxLayout()
        cycles_samples_layout = QHBoxLayout()
        self.cycles_samples_label = QLabel("Samples:")
        self.cycles_samples_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cycles_samples = QSpinBox()
        self.cycles_samples.setRange(1, 10000)
        cycles_samples_layout.addWidget(self.cycles_samples_label)
        cycles_samples_layout.addWidget(self.cycles_samples)

        cycles_denoising_layout = QHBoxLayout()
        self.cycles_denoising_label = QLabel("Denoising:")
        self.cycles_denoising_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cycles_denoising = QCheckBox()
        cycles_denoising_layout.addWidget(self.cycles_denoising_label)
        cycles_denoising_layout.addWidget(self.cycles_denoising)

        cycles_device_layout = QHBoxLayout()
        self.cycles_device_label = QLabel("Device:")
        self.cycles_device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cycles_device = QComboBox()
        self.cycles_device.addItems(["CPU", "GPU"])
        self.cycles_device.setCurrentIndex(-1)
        cycles_device_layout.addWidget(self.cycles_device_label)
        cycles_device_layout.addWidget(self.cycles_device)

        cycles_threads_layout = QHBoxLayout()
        self.cycles_threads_label = QLabel("Threads:")
        self.cycles_threads_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.cycles_threads = QSpinBox()
        self.cycles_threads.setRange(1, utils.get_cpu_count())
        self.cycles_threads_label.setHidden(True)
        self.cycles_threads.setHidden(True)
        cycles_threads_layout.addWidget(self.cycles_threads_label)
        cycles_threads_layout.addWidget(self.cycles_threads)

        cycles_layout.addLayout(cycles_samples_layout)
        cycles_layout.addLayout(cycles_denoising_layout)
        cycles_layout.addLayout(cycles_device_layout)
        cycles_layout.addLayout(cycles_threads_layout)
        self.cycles_settings.setLayout(cycles_layout)
        settings_layout.addWidget(self.cycles_settings)

        # Eevee settings
        self.eevee_settings = QGroupBox("Eevee settings")
        eevee_layout = QVBoxLayout()
        eevee_samples_layout = QHBoxLayout()
        self.eevee_samples_label = QLabel("Samples:")
        self.eevee_samples_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.eevee_samples = QSpinBox()
        self.eevee_samples.setRange(1, 10000)
        eevee_samples_layout.addWidget(self.eevee_samples_label)
        eevee_samples_layout.addWidget(self.eevee_samples)
        eevee_layout.addLayout(eevee_samples_layout)
        self.eevee_settings.setLayout(eevee_layout)
        settings_layout.addWidget(self.eevee_settings)

        # Connect signals
        self.render_type.currentIndexChanged.connect(self.update_render_type)
        self.output_folder_button.clicked.connect(self.update_output_folder)
        self.render_engine.currentIndexChanged.connect(self.update_render_engine)
        self.cycles_device.currentIndexChanged.connect(self.update_cycles_device)

        self.cycles_settings.setHidden(True)
        self.eevee_settings.setHidden(True)

        right_panel_layout.addLayout(settings_layout)
        self.right_panel.setLayout(right_panel_layout)
        self.right_layout.addWidget(self.right_panel)
        self.right_layout.addStretch()  # Prevent vertical stretching

    def update_render_type(self):
        logger.debug(f"Updating render type to {self.render_type.currentText()}")
        try:
            if not self.current_project:
                logger.warning("No current project selected")
                return

            settings = self.current_project.settings
            if self.render_type.currentText() == "Image":
                self.frame_current_label.setHidden(False)
                self.frame_current.setHidden(False)
                self.frame_start_label.setHidden(True)
                self.frame_start.setHidden(True)
                self.frame_end_label.setHidden(True)
                self.frame_end.setHidden(True)
                self.frame_step_label.setHidden(True)
                self.frame_step.setHidden(True)
                self.fps_value_label.setHidden(True)
                self.fps_value.setHidden(True)
                self.fps_base_label.setHidden(True)
                self.fps_base.setHidden(True)

                self.output_format_combobox.clear()
                self.output_format_combobox.addItems(settings["File Formats Image"])
                self.frame_current.setValue(settings["Frame"])

            elif self.render_type.currentText() == "Movie":
                self.frame_current_label.setHidden(True)
                self.frame_current.setHidden(True)
                self.frame_start_label.setHidden(False)
                self.frame_start.setHidden(False)
                self.frame_end_label.setHidden(False)
                self.frame_end.setHidden(False)
                self.frame_step_label.setHidden(False)
                self.frame_step.setHidden(False)
                self.fps_value_label.setHidden(False)
                self.fps_value.setHidden(False)
                self.fps_base_label.setHidden(False)
                self.fps_base.setHidden(False)

                self.output_format_combobox.clear()
                self.output_format_combobox.addItems(settings["File Formats Movie"])
                self.frame_start.setValue(settings["Frame Start"])
                self.frame_end.setValue(settings["Frame End"])
                self.frame_step.setValue(settings["Frame Step"])

            if self.output_format_combobox.findText(settings["File Format"]) != -1:
                self.output_format_combobox.setCurrentIndex(
                    self.output_format_combobox.findText(settings["File Format"])
                )
        except Exception as e:
            logger.error(f"Error updating render type: {str(e)}")

    def update_render_engine(self):
        logger.debug(f"Updating render engine to {self.render_engine.currentText()}")
        try:
            if not self.current_project:
                logger.warning("No current project selected")
                return

            settings = self.current_project.settings
            if self.render_engine.currentText() == "CYCLES":
                self.cycles_settings.setHidden(False)
                self.eevee_settings.setHidden(True)
                self.cycles_samples.setValue(settings["CYCLES Samples"])
                self.cycles_denoising.setChecked(settings["Denoising"])
                self.cycles_device.setCurrentIndex(self.cycles_device.findText(settings["Device"]))
                if settings["Device"] == "CPU":
                    self.cycles_threads_label.setHidden(False)
                    self.cycles_threads.setHidden(False)
            else:
                self.cycles_settings.setHidden(True)
                self.eevee_settings.setHidden(False)
                self.eevee_samples.setValue(settings["EEVEE Samples"])
        except Exception as e:
            logger.error(f"Error updating render engine: {str(e)}")

    def update_cycles_device(self):
        logger.debug(f"Updating cycles device to {self.cycles_device.currentText()}")
        try:
            if self.cycles_device.currentText() == "CPU":
                self.cycles_threads_label.setHidden(False)
                self.cycles_threads.setHidden(False)
            else:
                self.cycles_threads_label.setHidden(True)
                self.cycles_threads.setHidden(True)
        except Exception as e:
            logger.error(f"Error updating cycles device: {str(e)}")

    def update_output_folder(self):
        logger.debug("Opening output folder dialog")
        try:
            folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
            if folder:
                self.output_folder.setText(folder)
                logger.info(f"Output folder set to: {folder}")
        except Exception as e:
            logger.error(f"Error selecting output folder: {str(e)}")

    def update_blender_bin(self):
        logger.debug("Updating blender binary")
        try:
            self.current_bin = utils.transform_path_to_standard(self.blender_bin.currentText())
            if self.current_bin:
                self.blender_version_text.setText(self.blender_paths.get(self.current_bin, ""))
                utils.set_config_value("current_bin", self.current_bin)
                utils.set_blender_in_path(self.current_bin)
                logger.info(f"Blender binary updated to: {self.current_bin}")
        except Exception as e:
            logger.error(f"Error updating blender binary: {str(e)}")

    def add_blend_file(self):
        logger.debug("Adding blend file")
        try:
            file_dialog = QFileDialog()
            file_paths, _ = file_dialog.getOpenFileNames(
                self, "Add .blend file", "", "Blender Files (*.blend);;All Files (*)"
            )

            for file_path in file_paths:
                file_path = utils.transform_path_to_standard(file_path)
                project = Project(file_path)
                item = QListWidgetItem(utils.get_file_name_from_path(project.file_path))
                item.setData(Qt.UserRole, project.unique_name)
                self.blend_files_list.addItem(item)

                project.settings = self.blender_manager.get_settings_from_project(file_path)
                self.projects[project.unique_name] = project
                logger.info(f"Added blend file: {file_path}")
        except Exception as e:
            logger.error(f"Error adding blend file: {str(e)}")
            self.update_output(f"Error adding blend file: {str(e)}")

    def add_blender_bin(self):
        logger.debug("Adding blender binary")
        try:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self, "Add blender.exe file", "", "blender.exe (*.exe)"
            )
            file_path = utils.transform_path_to_standard(file_path)

            if file_path and file_path not in self.blender_paths:
                if utils.is_blender_bin(file_path):
                    self.blender_paths[file_path] = utils.get_blender_version(file_path)
                    utils.set_config_value("bin_paths", self.blender_paths)
                    self.blender_bin.clear()
                    self.blender_bin.addItems(self.blender_paths.keys())
                    self.blender_bin.setCurrentIndex(-1)
                    logger.info(f"Added new blender binary: {file_path}")
                else:
                    logger.warning(f"Invalid blender binary: {file_path}")
                    self.update_output(f"Path {file_path} is not a valid blender.exe")
            else:
                logger.warning(f"Blender binary already added or empty: {file_path}")
                self.update_output(f"Path {file_path} already added or invalid")
        except Exception as e:
            logger.error(f"Error adding blender binary: {str(e)}")
            self.update_output(f"Error adding blender binary: {str(e)}")

    # TODO: Fix other project get another settings in cycles
    def show_file_details(self, item):
        logger.debug(f"Showing details for file: {item.text()}")
        try:
            if self.current_project:
                self.update_render_settings()

            self.current_project = self.projects[item.data(Qt.UserRole)]
            preview_image_path = utils.path_to_thumbnail(self.current_project.unique_name)

            if preview_image_path and os.path.exists(preview_image_path):
                try:
                    pixmap = QPixmap(preview_image_path)
                    if not pixmap.isNull():
                        self.preview.setPixmap(QPixmap(preview_image_path))
                        # self.preview.setPixmap(pixmap.scaled(
                        #     self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                        # ))
                    else:
                        self.preview.setText("Invalid preview image")
                        logger.warning(f"Invalid preview image: {preview_image_path}")
                except Exception as e:
                    logger.error(f"Error loading preview image: {str(e)}")
                    self.preview.setText("Error loading preview")
            else:
                self.preview.setText("Preview not available")
                logger.info(f"No preview available for: {self.current_project.unique_name}")

            settings = self.current_project.settings
            self.render_type.setCurrentIndex(self.render_type.findText("Image"))
            self.frame_current.setValue(settings["Frame"])

            self.render_type.setCurrentIndex(self.render_type.findText("Movie"))
            self.frame_start.setValue(settings["Frame Start"])
            self.frame_end.setValue(settings["Frame End"])
            self.frame_step.setValue(settings["Frame Step"])
            self.fps_value.setValue(settings["FPS"])
            self.fps_base.setValue(settings["FPS Base"])

            if settings["File Format"] in settings["File Formats Image"]:
                self.render_type.setCurrentIndex(self.render_type.findText("Image"))
            elif settings["File Format"] in settings["File Formats Movie"]:
                self.render_type.setCurrentIndex(self.render_type.findText("Movie"))
            else:
                logger.error(f"Unknown file format: {settings['File Format']}")
                raise ValueError(f"Unknown file format: {settings['File Format']}")

            self.resolution_x.setValue(settings["ResolutionX"])
            self.resolution_y.setValue(settings["ResolutionY"])
            self.resolution_scale.setValue(settings["Resolution Scale"])
            self.render_engine.setCurrentIndex(self.render_engine.findText(settings["Render Engine"]))

            self.cycles_threads.setValue(
                settings["Threads"] if settings["Threads"] != 0 else utils.get_cpu_count()
            )

            self.output_format_combobox.setCurrentIndex(
                self.output_format_combobox.findText(settings["File Format"])
            )
            self.output_folder.setText(settings["Output Path"])

            logger.info(f"Displayed details for project: {self.current_project.unique_name}")
        except Exception as e:
            logger.error(f"Error showing file details: {str(e)}")
            self.update_output(f"Error showing file details: {str(e)}")

    def update_project_preview(self):
        logger.debug("Updating project preview")
        try:
            if self.current_project:
                self.blender_manager.render_project_thumbnail(self.current_project)
                logger.info(f"Requested preview update for: {self.current_project.unique_name}")
            else:
                logger.warning("No project selected for preview update")
        except Exception as e:
            logger.error(f"Error updating project preview: {str(e)}")
            self.update_output(f"Error updating preview: {str(e)}")

    def update_render_settings(self):
        logger.debug("Updating render settings")
        try:
            if not self.current_project:
                logger.warning("No current project to update settings")
                return

            settings = self.current_project.settings
            settings["Frame Start"] = self.frame_start.value()
            settings["Frame End"] = self.frame_end.value()
            settings["Frame Step"] = self.frame_step.value()
            settings["Frame"] = self.frame_current.value()
            settings["ResolutionX"] = self.resolution_x.value()
            settings["ResolutionY"] = self.resolution_y.value()
            settings["Resolution Scale"] = self.resolution_scale.value()
            settings["File Format"] = self.output_format_combobox.currentText()
            settings["Output Path"] = self.output_folder.text()
            settings["Render Engine"] = self.render_engine.currentText()
            settings["CYCLES Samples"] = self.cycles_samples.value()
            settings["Denoising"] = self.cycles_denoising.isChecked()
            settings["Device"] = self.cycles_device.currentText()
            settings["Threads"] = self.cycles_threads.value()
            settings["EEVEE Samples"] = self.eevee_samples.value()

            self.current_project.settings = settings.copy()
            logger.info(f"Updated render settings for: {self.current_project.unique_name}")
        except Exception as e:
            logger.error(f"Error updating render settings: {str(e)}")
            self.update_output(f"Error updating render settings: {str(e)}")

    def update_output(self, message):
        logger.info(f"Output message: {message}")
        try:
            self.progress_output.append(message)
        except Exception as e:
            logger.error(f"Error updating output: {str(e)}")

    def start_render_queue(self):
        logger.debug("Starting render queue")
        try:
            self.update_render_settings()
            projects_to_render = [
                self.projects[self.blend_files_list.item(index).data(Qt.UserRole)]
                for index in range(self.blend_files_list.count())
            ]

            if not projects_to_render:
                logger.warning("No projects to render")
                self.update_output("No projects to render")
                return

            self.blender_manager.start_render_projects(projects_to_render, False)
            logger.info(f"Started render queue with {len(projects_to_render)} projects")
        except Exception as e:
            logger.error(f"Error starting render queue: {str(e)}")
            self.update_output(f"Error starting render queue: {str(e)}")


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
