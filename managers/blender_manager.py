import json
import subprocess
import threading
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Callable, Optional

import bpy
from PyQt5.QtCore import QObject

from util import utils

# Configure logging
logger = logging.getLogger('BlenderManager')
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


# TODO: Add script for Movie render type
class BlenderManager(QObject):
    def __init__(self, parent=None):
        """Initialize BlenderManager with a parent QObject."""
        super().__init__(parent)
        self.qt_signal = parent.signal if parent else None
        logger.info("Initializing BlenderManager")
        if not self.qt_signal:
            logger.warning("No Qt signal provided, signal emissions will be ignored")

    def render_project_thumbnail(self, project) -> None:
        """Start rendering a thumbnail for the given project in a separate thread."""
        if not project or not hasattr(project, 'file_path') or not hasattr(project, 'unique_name'):
            logger.error("Invalid project object provided for thumbnail rendering")
            if self.qt_signal:
                self.qt_signal.emit("Error: Invalid project object")
            return

        logger.info(f"Starting thumbnail render for project: {project.file_path}")
        if self.qt_signal:
            self.qt_signal.emit(f"Start render thumbnail: {project.file_path}")

        try:
            render_thread = threading.Thread(
                target=self._start_render_thumbnail,
                args=(project, lambda: self._on_render_thumbnails_complete([]))
            )
            render_thread.start()
            logger.debug(f"Started render thread for thumbnail: {project.file_path}")
        except Exception as e:
            logger.error(f"Error starting thumbnail render thread for {project.file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error starting thumbnail render: {str(e)}")

    def start_render_projects(self, projects: List, isCreatingThumbnails: bool) -> None:
        """Start rendering projects or thumbnails in a separate thread."""
        if not isinstance(projects, list):
            logger.error(f"Invalid projects type: {type(projects)}, expected list")
            if self.qt_signal:
                self.qt_signal.emit("Error: Projects must be a list")
            return
        if not projects:
            logger.warning("Empty projects list provided for rendering")
            if self.qt_signal:
                self.qt_signal.emit("No projects to render")
            return

        logger.info(f"Starting render for {len(projects)} projects, isCreatingThumbnails: {isCreatingThumbnails}")
        try:
            # Запускаем рендер в отдельном потоке
            render_thread = threading.Thread(
                target=self._render_next_thumbnail if isCreatingThumbnails else self._render_next,
                args=(projects,)
            )
            render_thread.start()
            logger.debug("Started render thread for projects")
        except Exception as e:
            logger.error(f"Error starting render thread: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error starting render: {str(e)}")

    def _render_next_thumbnail(self, projects_without_thumbnails: List) -> None:
        """Render the next thumbnail in the queue."""
        if not projects_without_thumbnails:
            # Если очередь пуста, завершаем выполнение
            logger.info("All thumbnail renders completed")
            if self.qt_signal:
                self.qt_signal.emit("All thumbnail renders completed.\n")
            return

        # Берем первый файл из очереди
        project = projects_without_thumbnails.pop(0)
        if not hasattr(project, 'file_path') or not hasattr(project, 'unique_name'):
            logger.error("Invalid project object in thumbnail queue")
            if self.qt_signal:
                self.qt_signal.emit("Error: Invalid project object")
            self._on_render_thumbnails_complete(projects_without_thumbnails)
            return

        # Выводим информацию о начале рендера
        logger.info(f"Starting thumbnail render: {project.file_path}")
        if self.qt_signal:
            self.qt_signal.emit(f"Start render thumbnail: {project.file_path}")

        try:
            self._start_render_thumbnail(project, lambda: self._on_render_thumbnails_complete(projects_without_thumbnails))
        except Exception as e:
            logger.error(f"Error rendering thumbnail for {project.file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error rendering thumbnail: {str(e)}")
            self._on_render_thumbnails_complete(projects_without_thumbnails)

    def _start_render_thumbnail(self, project, callback: Callable) -> None:
        """Execute the thumbnail rendering process for a project."""
        file_path = project.file_path
        unique_name = project.unique_name
        logger.debug(f"Preparing to render thumbnail for {file_path} with unique name {unique_name}")

        # Проверяем существование файлов
        if not utils.is_path_exists(file_path):
            logger.error(f"Project file not found: {file_path}")
            if self.qt_signal:
                self.qt_signal.emit(f"File {file_path} not found.")
            callback()
            return

        script_path = utils.transform_path_to_standard(
            utils.get_config_value("work_directory") + "\\scripts\\render_preview_script.py"
        )
        if not utils.is_path_exists(script_path):
            logger.error(f"Render script not found: {script_path}")
            if self.qt_signal:
                self.qt_signal.emit("File render_preview_script.py not found.")
            callback()
            return

        # Команда для запуска Blender
        blender_executable = utils.get_config_value("current_bin")
        if not blender_executable or not utils.is_path_exists(blender_executable):
            logger.error(f"Blender executable not found: {blender_executable}")
            if self.qt_signal:
                self.qt_signal.emit("Blender executable not found.")
            callback()
            return

        command = [
            blender_executable,
            "--background",  # Запуск в фоновом режиме
            "--python", "./scripts/render_preview_script.py",  # Скрипт для выполнения
            "--",  # Разделитель для аргументов скрипта
            file_path,
            unique_name,
        ]
        logger.debug(f"Executing command: {' '.join(command)}")

        try:
            with subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffering
                    universal_newlines=True
            ) as process:
                # Function to read output in real time
                def read_output(pipe, label: str):
                    try:
                        for line in iter(pipe.readline, ''):
                            if line:
                                logger.debug(f"{label}: {line.strip()}")
                                if self.qt_signal:
                                    self.qt_signal.emit(f"{label}: {line.strip()}")
                    except Exception as e:
                        logger.error(f"Error reading {label} for {file_path}: {str(e)}")

                logger.info(f"Blender process started for thumbnail: {file_path}")
                if self.qt_signal:
                    self.qt_signal.emit(f"Blender starts with file: {file_path}")

                # Start threads to read stdout and stderr
                stdout_thread = threading.Thread(target=read_output, args=(process.stdout, "STDOUT"))
                stderr_thread = threading.Thread(target=read_output, args=(process.stderr, "STDERR"))
                stdout_thread.start()
                stderr_thread.start()

                # Wait for process to complete
                process.wait()
                stdout_thread.join()
                stderr_thread.join()

                if process.returncode != 0:
                    logger.error(f"Thumbnail render failed for {file_path}, return code: {process.returncode}")
                    if self.qt_signal:
                        self.qt_signal.emit(f"Thumbnail render failed with code {process.returncode}")
                else:
                    logger.info(f"Thumbnail render completed successfully for {file_path}")
                    if self.qt_signal:
                        self.qt_signal.emit(f"Thumbnail render completed for {file_path}")

        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error rendering thumbnail for {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Subprocess error rendering thumbnail: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error rendering thumbnail for {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Unexpected error rendering thumbnail: {str(e)}")

        callback()

    def _on_render_thumbnails_complete(self, projects: List) -> None:
        """Handle completion of a thumbnail render and proceed to the next."""
        # Выводим информацию о завершении рендера
        logger.info("Thumbnail render completed")
        if self.qt_signal:
            self.qt_signal.emit("Render ends\n")

        # Запускаем рендер следующего файла
        self._render_next_thumbnail(projects)

    def _render_next(self, projects_to_render: List) -> None:
        """Render the next project in the queue."""
        if not projects_to_render:
            # Если очередь пуста, завершаем выполнение
            logger.info("All renders completed")
            if self.qt_signal:
                self.qt_signal.emit("All renders completed.\n")
            return

        # Берем первый файл из очереди
        project = projects_to_render.pop(0)
        if not hasattr(project, 'file_path') or not hasattr(project, 'settings'):
            logger.error("Invalid project object in render queue")
            if self.qt_signal:
                self.qt_signal.emit("Error: Invalid project object")
            self._on_render_complete(projects_to_render)
            return

        # Выводим информацию о начале рендера
        logger.info(f"Starting render: {project.file_path}")
        if self.qt_signal:
            self.qt_signal.emit(f"Start render: {project.file_path}")

        try:
            self._start_render(project, lambda: self._on_render_complete(projects_to_render))
        except Exception as e:
            logger.error(f"Error rendering project {project.file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error rendering project: {str(e)}")
            self._on_render_complete(projects_to_render)

    def _start_render(self, project, callback: Callable) -> None:
        """Execute the rendering process for a project."""
        file_path = project.file_path
        settings = project.settings
        logger.debug(f"Preparing to render project: {file_path}")

        # Проверяем существование файлов
        if not utils.is_path_exists(file_path):
            logger.error(f"Project file not found: {file_path}")
            if self.qt_signal:
                self.qt_signal.emit(f"File {file_path} not found.")
            callback()
            return

        script_path = utils.transform_path_to_standard(
            utils.get_config_value("work_directory") + "\\scripts\\render_script.py"
        )
        if not utils.is_path_exists(script_path):
            logger.error(f"Render script not found: {script_path}")
            if self.qt_signal:
                self.qt_signal.emit("File render_script.py not found.")
            callback()
            return

        # Преобразуем настройки в JSON-строку
        try:
            settings_json = json.dumps(settings)
        except TypeError as e:
            logger.error(f"Failed to serialize settings for {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error serializing settings: {str(e)}")
            callback()
            return

        # Команда для запуска Blender
        blender_executable = utils.get_config_value("current_bin")
        if not blender_executable or not utils.is_path_exists(blender_executable):
            logger.error(f"Blender executable not found: {blender_executable}")
            if self.qt_signal:
                self.qt_signal.emit("Blender executable not found.")
            callback()
            return

        command = [
            blender_executable,
            "--background",  # Запуск в фоновом режиме
            "--python", "./scripts/render_script.py",  # Скрипт для выполнения
            "--",  # Разделитель для аргументов скрипта
            file_path,
            settings_json,
        ]
        logger.debug(f"Executing command: {' '.join(command)}")

        try:
            with subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line buffering
                    universal_newlines=True
            ) as process:
                # Function to read output in real time
                def read_output(pipe, label: str):
                    try:
                        for line in iter(pipe.readline, ''):
                            if line:
                                logger.debug(f"{label}: {line.strip()}")
                                if self.qt_signal:
                                    self.qt_signal.emit(f"{label}: {line.strip()}")
                    except Exception as e:
                        logger.error(f"Error reading {label} for {file_path}: {str(e)}")

                logger.info(f"Blender process started for render: {file_path}")
                if self.qt_signal:
                    self.qt_signal.emit(f"Blender starts with file: {file_path}")

                # Start threads to read stdout and stderr
                stdout_thread = threading.Thread(target=read_output, args=(process.stdout, "STDOUT"))
                stderr_thread = threading.Thread(target=read_output, args=(process.stderr, "STDERR"))
                stdout_thread.start()
                stderr_thread.start()

                # Wait for process to complete
                process.wait()
                stdout_thread.join()
                stderr_thread.join()

                if process.returncode != 0:
                    logger.error(f"Render failed for {file_path}, return code: {process.returncode}")
                    if self.qt_signal:
                        self.qt_signal.emit(f"Render failed with code {process.returncode}")
                else:
                    logger.info(f"Render completed successfully for {file_path}")
                    if self.qt_signal:
                        self.qt_signal.emit(f"Render completed for {file_path}")

        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error rendering project {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Subprocess error rendering project: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error rendering project {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Unexpected error rendering project: {str(e)}")

        callback()

    def _on_render_complete(self, projects_to_render: List) -> None:
        """Handle completion of a project render and proceed to the next."""
        # Выводим информацию о завершении рендера
        logger.info("Project render completed")
        if self.qt_signal:
            self.qt_signal.emit("Render ends\n")

        # Запускаем рендер следующего файла
        self._render_next(projects_to_render)

    def get_settings_from_project(self, file_path: str) -> Optional[dict]:
        """Retrieve rendering settings from a Blender project file."""
        if not isinstance(file_path, str):
            logger.error(f"Invalid file path type: {type(file_path)}, expected string")
            if self.qt_signal:
                self.qt_signal.emit(f"Error: Invalid file path type: {type(file_path)}")
            return None
        if not file_path:
            logger.error("Empty file path provided")
            if self.qt_signal:
                self.qt_signal.emit("Error: Empty file path")
            return None
        if not utils.is_path_exists(file_path):
            logger.error(f"Project file not found: {file_path}")
            if self.qt_signal:
                self.qt_signal.emit(f"File {file_path} not found.")
            return None

        logger.info(f"Retrieving settings from project: {file_path}")
        try:
            bpy.ops.wm.open_mainfile(filepath=file_path)
            scene = bpy.context.scene

            file_formats = []
            enum_formats = scene.render.image_settings.bl_rna.properties['file_format'].enum_items
            for item in enum_formats:
                file_formats.append(item.name)

            # Dict
            settings = {
                # Scene
                # "Scene Name": scene.name,
                # "Camera": scene.camera.name,
                # "Cameras": cameras,

                # Format
                "ResolutionX": scene.render.resolution_x,
                "ResolutionY": scene.render.resolution_y,
                "Resolution Scale": scene.render.resolution_percentage,
                "FPS": scene.render.fps,
                "FPS Base": scene.render.fps_base,

                # Frame range
                "Frame Start": scene.frame_start,
                "Frame End": scene.frame_end,
                "Frame Step": scene.frame_step,
                "Frame": scene.frame_current,

                # TODO: Only eevee/cycles engines
                # Engines
                "Render Engine": scene.render.engine,

                # CYCLES
                "CYCLES Samples": scene.cycles.samples if hasattr(scene, 'cycles') else 128,
                "Denoising": scene.cycles.use_denoising if hasattr(scene, 'cycles') else False,
                "Device": scene.cycles.device if hasattr(scene, 'cycles') else "CPU",
                "Threads": 0,

                # EEVEE
                "EEVEE Samples": scene.eevee.taa_render_samples if hasattr(scene, 'eevee') else 64,

                # Output
                "File Format": scene.render.image_settings.file_format,
                "File Formats Image": file_formats[:-3],
                "File Formats Movie": ['AVI_JPEG', 'AVI_RAW', 'FFMPEG'],  # Костыль, тк блендер для видео форматов использует другие названия
                # "File Formats Movie": file_formats[-3:],
                "Output Path": scene.render.filepath,
            }

            logger.info(f"Successfully retrieved settings from {file_path}")
            return settings

        except Exception as e:
            logger.error(f"Error retrieving settings from {file_path}: {str(e)}")
            if self.qt_signal:
                self.qt_signal.emit(f"Error retrieving settings: {str(e)}")
            return None