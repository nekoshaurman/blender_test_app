import json
import subprocess
import threading

import bpy
from PyQt5.QtCore import QObject

from util import utils


# TODO: Добавить рендер movie
class BlenderManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.qt_signal = parent.signal

    def render_project_thumbnail(self, project):
        self.qt_signal.emit(f"Start render thumbnail: {project.file_path}")

        render_thread = threading.Thread(target=self._start_render_thumbnail, args=(project, lambda: self._on_render_thumbnails_complete([]),))

        render_thread.start()

    def start_render_projects(self, projects, isCreatingThumbnails):
        # Запускаем рендер в отдельном потоке
        if isCreatingThumbnails:
            render_thread = threading.Thread(target=self._render_next_thumbnail, args=(projects,))

        else:
            render_thread = threading.Thread(target=self._render_next, args=(projects,))

        render_thread.start()

    def _render_next_thumbnail(self, projects_without_thumbnails):
        if not projects_without_thumbnails:
            # Если очередь пуста, завершаем выполнение
            # self.qt_signal.emit("All thumbnail renders completed.\n")
            return

        # Берем первый файл из очереди
        project = projects_without_thumbnails.pop(0)

        # Выводим информацию о начале рендера
        self.qt_signal.emit(f"Start render thumbnail: {project.file_path}")

        # Запускаем рендер через subprocess
        self._start_render_thumbnail(project, lambda: self._on_render_thumbnails_complete(projects_without_thumbnails))

    def _start_render_thumbnail(self, project, callback):
        file_path = project.file_path
        unique_name = project.unique_name
        # Проверяем существование файлов
        if not utils.is_path_exists(file_path):
            self.qt_signal.emit(f"File {file_path} not founded.")
            return
        if not utils.is_path_exists(utils.transform_path_to_standard(utils.get_config_value("work_directory") + "\\scripts\\render_preview_script.py")):
            self.qt_signal.emit("File render_preview_script.py not founded.")
            return

        # Команда для запуска Blender
        blender_executable = utils.get_config_value("current_bin")  # Используемый блендер

        if not utils.is_path_exists(blender_executable):
            self.qt_signal.emit("blender.exe (bin) not find")
            return

        command = [
            blender_executable,
            "--background",  # Запуск в фоновом режиме
            "--python", "./scripts/render_preview_script.py",  # Скрипт для выполнения
            "--",  # Разделитель для аргументов скрипта
            file_path,
            unique_name,
        ]

        # Запускаем процесс
        with subprocess.Popen(
                command,
        ) as process:
            # Проверяем статус завершения процесса
            # self.qt_signal.emit(f"Процесс завершился с кодом {process.returncode}")
            self.qt_signal.emit(f"Blender starts with file: {file_path}")
            # if process.returncode == 0:
            #     # print(f"Ошибка выполнения: Процесс завершился с кодом {process.returncode}")
            #     self.qt_signal.emit(f"Ошибка выполнения: Процесс завершился с кодом {process.returncode}")
            # else:
            #     # print("Процесс успешно завершен.")
            #     self.qt_signal.emit("Процесс успешно завершен.")

        callback()

    def _on_render_thumbnails_complete(self, projects):
        # Выводим информацию о завершении рендера
        self.qt_signal.emit("Render ends\n")

        # Запускаем рендер следующего файла
        self._render_next_thumbnail(projects)

    def _render_next(self, projects_to_render):
        if not projects_to_render:
            # Если очередь пуста, завершаем выполнение
            self.qt_signal.emit("All renders completed.\n")
            return

        # Берем первый файл из очереди
        # file_path, file_id = files_to_render.pop(0)
        project = projects_to_render.pop(0)

        # Выводим информацию о начале рендера
        # self.progress_signal.emit(f"Start render: {file_path}\n")
        self.qt_signal.emit(f"Start render: {project.file_path}")

        # Запускаем рендер через subprocess
        # self._start_render(file_path, self.file_settings[file_id], lambda: self._on_render_complete(files_to_render))
        self._start_render(project, lambda: self._on_render_complete(projects_to_render))

    # TODO: Надо сделать отслеживание по логам блендера
    def _start_render(self, project, callback):
        file_path = project.file_path
        settings = project.settings
        # Проверяем существование файлов
        if not utils.is_path_exists(file_path):
            self.qt_signal.emit(f"Файл {file_path} не найден.")
            return
        if not utils.is_path_exists("../scripts/render_script.py"):
            self.qt_signal.emit("Файл render_script.py не найден.")
            return

        # Преобразуем настройки в JSON-строку
        settings_json = json.dumps(settings)

        # Команда для запуска Blender
        blender_executable = utils.get_config_value("current_bin")  # Используемый блендер
        command = [
            blender_executable,
            "--background",  # Запуск в фоновом режиме
            "--python", "render_script.py",  # Скрипт для выполнения
            "--",  # Разделитель для аргументов скрипта
            file_path,
            settings_json,
        ]

        # Запускаем процесс
        with subprocess.Popen(
                command,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                # text=True,  # Чтение текста вместо байтов
        ) as process:
            # Функция для чтения вывода в реальном времени
            # def read_output(pipe, label):
            #     for line in iter(pipe.readline, ""):
            #         self.qt_signal.emit(f"{label}: {line.strip()}")

            # # Читаем stdout и stderr параллельно
            # stdout_thread = threading.Thread(target=read_output, args=(process.stdout, "STDOUT"))
            # stderr_thread = threading.Thread(target=read_output, args=(process.stderr, "STDERR"))
            #
            # stdout_thread.start()
            # stderr_thread.start()
            #
            # # Ждем завершения потоков
            # stdout_thread.join()
            # stderr_thread.join()

            # Проверяем статус завершения процесса
            # self.qt_signal.emit(f"Процесс завершился с кодом {process.returncode}")
            self.qt_signal.emit(f"Blender starts with file: {file_path}")
            # if process.returncode != 0:
            #     # print(f"Ошибка выполнения: Процесс завершился с кодом {process.returncode}")
            #     self.qt_signal.emit(f"Ошибка выполнения: Процесс завершился с кодом {process.returncode}")
            # else:
            #     # print("Процесс успешно завершен.")
            #     self.qt_signal.emit("Процесс успешно завершен.")

        callback()

    def _on_render_complete(self, projects_to_render):
        # Выводим информацию о завершении рендера
        self.qt_signal.emit(f"Render ends\n")

        # Запускаем рендер следующего файла
        self._render_next(projects_to_render)

    def get_settings_from_project(self, file_path):
        try:
            bpy.ops.wm.open_mainfile(filepath=file_path)
            scene = bpy.context.scene

            file_formats = []
            enum_formats = scene.render.image_settings.bl_rna.properties['file_format'].enum_items
            for item in enum_formats:
                file_formats.append(item.name)

            # cameras = [obj.name for obj in bpy.data.objects if obj.type == 'CAMERA']

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

                # TODO: Исключать движки рендера кроме eevee и cycles
                # Engines
                "Render Engine": scene.render.engine,

                # CYCLES
                "CYCLES Samples": scene.cycles.samples,
                "Denoising": scene.cycles.use_denoising,
                "Device": scene.cycles.device,
                "Threads": 0,

                # EEVEE
                "EEVEE Samples": scene.eevee.taa_render_samples,

                # Output
                "File Format": scene.render.image_settings.file_format,
                "File Formats Image": file_formats[:-3],
                "File Formats Movie": ['AVI_JPEG', 'AVI_RAW', 'FFMPEG'],  # Костыль, тк блендер для видео форматов использует другие названия
                # "File Formats Movie": file_formats[-3:],
                "Output Path": scene.render.filepath,
            }

            return settings

        except Exception as e:
            self.qt_signal.emit(f"Error: {str(e)}")
            return  # {"Error": str(e)}
