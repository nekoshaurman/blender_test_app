import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QSpinBox, QGroupBox, QSplitter, QComboBox, QCheckBox, QTextEdit, QDoubleSpinBox
)

import util.utils as utils
from managers.blender_manager import BlenderManager
from dto.project import Project


class BlenderInterface(QWidget):
    signal = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        self.blender_paths = utils.get_blender_paths()
        self.projects = {}
        self.file_settings = {}
        self.preview_paths = {}

        self.signal.connect(self.update_output)

        self.blender_manager = BlenderManager(self)

        self.main_layout = None
        self.left_layout = None
        self.right_layout = None

        self.blender_bin = None
        self.blender_bin_button = None

        self.blender_version_text = None

        self.start_render_button = None

        self.blend_file_button = None
        self.blend_files_list = None

        self.progress_output = None

        self.preview_window = None
        self.preview = None
        self.render_preview_button = None

        self.settings_window = None
        self.render_type = None

        self.frame_start_label = None
        self.frame_start = None
        self.frame_end_label = None
        self.frame_end = None
        self.frame_step_label = None
        self.frame_step = None

        self.fps_value_label = None
        self.fps_value = None
        self.fps_base_label = None
        self.fps_base = None

        self.frame_current_label = None
        self.frame_current = None

        self.format_settings = None

        self.resolution_x = None
        self.resolution_y = None
        self.resolution_scale = None

        self.output_settings = None

        self.output_format_combobox = None

        self.output_folder = None
        self.output_folder_button = None

        self.render_engine = None

        self.cycles_settings = None

        self.cycles_samples_label = None
        self.cycles_samples = None

        self.cycles_denoising_label = None
        self.cycles_denoising = None

        self.cycles_device_label = None
        self.cycles_device = None

        self.cycles_threads_label = None
        self.cycles_threads = None

        self.eevee_settings = None
        self.eevee_samples_label = None
        self.eevee_samples = None

        self.init_ui()

        self.current_project = None
        self.current_bin = None

    def init_ui(self):
        self.create_left_layout()
        self.create_right_layout()
        self.create_main_layout()

        self.setLayout(self.main_layout)

        self.setWindowTitle("Blender Interface")

    def create_main_layout(self):
        self.main_layout = QHBoxLayout()

        self.create_left_layout()
        self.create_right_layout()

        self.main_layout.addLayout(self.left_layout, 1)
        self.main_layout.addLayout(self.right_layout, 2)

    def create_left_layout(self):
        # Левая часть (настройки и список файлов)
        self.left_layout = QVBoxLayout()

        # Форма для рендера файлов
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

        # Форма версии выбранного блендера
        blender_version_layout = QHBoxLayout()

        blender_version_label = QLabel("Blender Version:")
        blender_version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.blender_version_text = QLabel("")

        blender_version_layout.addWidget(blender_version_label)
        blender_version_layout.addWidget(self.blender_version_text)

        # Форма для рендера файлов
        start_render_layout = QHBoxLayout()

        start_render_label = QLabel("Start render:")
        start_render_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.start_render_button = QPushButton("Start")
        self.start_render_button.clicked.connect(self.start_render_queue)

        start_render_layout.addWidget(start_render_label)
        start_render_layout.addWidget(self.start_render_button)

        # Форма для добавления .blend файлов
        blend_file_layout = QHBoxLayout()

        blend_file_label = QLabel("Добавить .blend файл:")
        blend_file_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.blend_file_button = QPushButton("Добавить .blend файл")
        self.blend_file_button.clicked.connect(self.add_blend_file)

        blend_file_layout.addWidget(blend_file_label)
        blend_file_layout.addWidget(self.blend_file_button)

        # Группировка форм
        settings_group = QGroupBox("Настройки")

        settings_layout = QVBoxLayout()

        settings_layout.addLayout(blender_bin_layout)
        settings_layout.addLayout(blender_version_layout)
        settings_layout.addLayout(start_render_layout)
        settings_layout.addLayout(blend_file_layout)

        settings_group.setLayout(settings_layout)
        settings_group.setFixedSize(800, 150)

        self.left_layout.addWidget(settings_group)

        # Список добавленных .blend файлов
        self.blend_files_list = QListWidget()
        self.blend_files_list.setSelectionMode(QListWidget.SingleSelection)

        self.blend_files_list.itemClicked.connect(self.show_file_details)
        self.left_layout.addWidget(self.blend_files_list)

        # Логи
        self.progress_output = QTextEdit()
        self.progress_output.setReadOnly(True)  # Запрещаем редактирование
        self.progress_output.setPlaceholderText("Logs")
        self.left_layout.addWidget(self.progress_output)
        # left_layout = LeftPanel(self).get_layout()

    def create_right_layout(self):
        # Правая часть (превью и настройки проекта)
        self.right_layout = QVBoxLayout()

        # Превью окно
        self.preview_window = QGroupBox("Превью")

        preview_layout = QVBoxLayout()

        self.preview = QLabel("Превью будет здесь")
        self.preview.setAlignment(Qt.AlignCenter)

        self.render_preview_button = QPushButton("Render Preview")
        self.render_preview_button.clicked.connect(self.update_project_preview)

        preview_layout.addWidget(self.preview)
        preview_layout.addWidget(self.render_preview_button)

        self.preview_window.setLayout(preview_layout)
        self.preview_window.setFixedSize(520, 300)
        self.preview_window.setHidden(True)  # Скрываем по умолчанию

        # Настройки проекта
        self.settings_window = QGroupBox("Настройки проекта")
        settings_layout = QVBoxLayout()

        # Выбор типа рендера (анимация или один кадр)
        render_type_layout = QHBoxLayout()
        render_type_label = QLabel("Тип рендера:")
        render_type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.render_type = QComboBox()
        self.render_type.addItems(["Movie", "Image"])
        self.render_type.setCurrentIndex(-1)

        render_type_layout.addWidget(render_type_label)
        render_type_layout.addWidget(self.render_type)
        settings_layout.addLayout(render_type_layout)
        # =============================================

        # Кадры (от и до для анимации, или один кадр)
        frame_start_layout = QHBoxLayout()
        self.frame_start_label = QLabel("Start:")
        self.frame_start_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.frame_start = QSpinBox()
        self.frame_start.setRange(0, 1048574)

        frame_start_layout.addWidget(self.frame_start_label)
        frame_start_layout.addWidget(self.frame_start)
        settings_layout.addLayout(frame_start_layout)
        # =============================================

        frame_end_layout = QHBoxLayout()
        self.frame_end_label = QLabel("End:")
        self.frame_end_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.frame_end = QSpinBox()
        self.frame_end.setRange(0, 1048574)

        frame_end_layout.addWidget(self.frame_end_label)
        frame_end_layout.addWidget(self.frame_end)
        settings_layout.addLayout(frame_end_layout)
        # =============================================

        frame_step_layout = QHBoxLayout()
        self.frame_step_label = QLabel("Step:")
        self.frame_step_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.frame_step = QSpinBox()
        self.frame_step.setRange(1, 1048574)

        frame_step_layout.addWidget(self.frame_step_label)
        frame_step_layout.addWidget(self.frame_step)
        settings_layout.addLayout(frame_step_layout)
        # =============================================

        frame_current_layout = QHBoxLayout()
        self.frame_current_label = QLabel("Current frame:")
        self.frame_current_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.frame_current = QSpinBox()

        frame_current_layout.addWidget(self.frame_current_label)
        frame_current_layout.addWidget(self.frame_current)
        settings_layout.addLayout(frame_current_layout)
        # =============================================

        fps_layout = QHBoxLayout()
        self.fps_value_label = QLabel("FPS:")
        self.fps_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.fps_value = QSpinBox()
        self.fps_value.setRange(1, 32767)

        fps_layout.addWidget(self.fps_value_label)
        fps_layout.addWidget(self.fps_value)
        settings_layout.addLayout(fps_layout)
        # =============================================

        fps_base_layout = QHBoxLayout()
        self.fps_base_label = QLabel("FPS Base:")
        self.fps_base_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.fps_base = QDoubleSpinBox()
        self.fps_base.setRange(1e-5, 1e6)
        self.fps_base.setSingleStep(0.1)

        fps_base_layout.addWidget(self.fps_base_label)
        fps_base_layout.addWidget(self.fps_base)
        settings_layout.addLayout(fps_base_layout)
        # =============================================

        # Format
        self.format_settings = QGroupBox("Format")

        format_layout = QVBoxLayout()

        # Разрешение (X и Y)
        resolution_x_layout = QHBoxLayout()
        resolution_x_label = QLabel("Resolution X:")
        resolution_x_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.resolution_x = QSpinBox()
        self.resolution_x.setRange(4, 65536)

        resolution_x_layout.addWidget(resolution_x_label)
        resolution_x_layout.addWidget(self.resolution_x)
        # =============================================

        resolution_y_layout = QHBoxLayout()
        resolution_y_label = QLabel("Y:")
        resolution_y_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.resolution_y = QSpinBox()
        self.resolution_y.setRange(4, 65536)

        resolution_y_layout.addWidget(resolution_y_label)
        resolution_y_layout.addWidget(self.resolution_y)
        # =============================================

        resolution_scale_layout = QHBoxLayout()
        resolution_scale_label = QLabel("%:")
        resolution_scale_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.resolution_scale = QSpinBox()
        self.resolution_scale.setRange(1, 32767)

        resolution_scale_layout.addWidget(resolution_scale_label)
        resolution_scale_layout.addWidget(self.resolution_scale)
        # =============================================

        format_layout.addLayout(resolution_x_layout)
        format_layout.addLayout(resolution_y_layout)
        format_layout.addLayout(resolution_scale_layout)

        self.format_settings.setLayout(format_layout)

        settings_layout.addWidget(self.format_settings)
        # =============================================

        self.output_settings = QGroupBox("Output")

        output_layout = QVBoxLayout()

        # Добавление выбора формата
        output_format_layout = QHBoxLayout()  # Горизонтальный layout для надписи и QComboBox
        output_format_label = QLabel("Output format:")  # Надпись "Формат"
        output_format_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Создаем QComboBox для выбора формата
        self.output_format_combobox = QComboBox()

        output_format_layout.addWidget(output_format_label)
        output_format_layout.addWidget(self.output_format_combobox)
        # =============================================

        # Выбор папки для сохранения результата
        output_folder_layout = QHBoxLayout()

        # Надпись "Папка для сохранения" занимает левую половину
        output_folder_label = QLabel("Папка для сохранения:")
        output_folder_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Горизонтальный layout для поля ввода и кнопки
        input_button_layout = QHBoxLayout()

        # Поле для ввода текста
        self.output_folder = QLineEdit()
        self.output_folder.setReadOnly(True)

        # Кнопка с фиксированным размером
        self.output_folder_button = QPushButton("...")
        self.output_folder_button.setFixedWidth(30)

        output_folder_layout.addWidget(output_folder_label, stretch=1)
        input_button_layout.addWidget(self.output_folder, stretch=2)
        input_button_layout.addWidget(self.output_folder_button)

        output_folder_layout.addLayout(input_button_layout, stretch=1)
        # =============================================

        output_layout.addLayout(output_format_layout)
        output_layout.addLayout(output_folder_layout)

        self.output_settings.setLayout(output_layout)

        settings_layout.addWidget(self.output_settings)
        # =============================================

        # Выбор движка (Cycles или Eevee)
        render_engine_layout = QHBoxLayout()

        render_engine_label = QLabel("Движок рендера:")
        render_engine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.render_engine = QComboBox()
        self.render_engine.addItems(["CYCLES", "BLENDER_EEVEE"])
        self.render_engine.setCurrentIndex(-1)

        render_engine_layout.addWidget(render_engine_label)
        render_engine_layout.addWidget(self.render_engine)

        settings_layout.addLayout(render_engine_layout)
        # =============================================

        # Настройки для Cycles
        self.cycles_settings = QGroupBox("Настройки Cycles")

        cycles_layout = QVBoxLayout()

        cycles_samples_layout = QHBoxLayout()

        self.cycles_samples_label = QLabel("Samples:")
        self.cycles_samples_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cycles_samples = QSpinBox()
        self.cycles_samples.setRange(1, 10000)

        cycles_samples_layout.addWidget(self.cycles_samples_label)
        cycles_samples_layout.addWidget(self.cycles_samples)
        # =============================================

        cycles_denoising_layout = QHBoxLayout()

        self.cycles_denoising_label = QLabel("Denoising:")
        self.cycles_denoising_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cycles_denoising = QCheckBox()

        cycles_denoising_layout.addWidget(self.cycles_denoising_label)
        cycles_denoising_layout.addWidget(self.cycles_denoising)
        # =============================================

        cycles_device_layout = QHBoxLayout()

        self.cycles_device_label = QLabel("Device:")
        self.cycles_device_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cycles_device = QComboBox()
        self.cycles_device.addItems(["CPU", "GPU"])
        self.cycles_device.setCurrentIndex(-1)

        cycles_device_layout.addWidget(self.cycles_device_label)
        cycles_device_layout.addWidget(self.cycles_device)
        # =============================================

        cycles_threads_layout = QHBoxLayout()

        self.cycles_threads_label = QLabel("Threads:")
        self.cycles_threads_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.cycles_threads = QSpinBox()
        self.cycles_threads.setRange(1, utils.get_cpu_count())

        self.cycles_threads_label.setHidden(True)
        self.cycles_threads.setHidden(True)

        cycles_threads_layout.addWidget(self.cycles_threads_label)
        cycles_threads_layout.addWidget(self.cycles_threads)
        # =============================================

        cycles_layout.addLayout(cycles_samples_layout)
        cycles_layout.addLayout(cycles_denoising_layout)
        cycles_layout.addLayout(cycles_device_layout)
        cycles_layout.addLayout(cycles_threads_layout)

        self.cycles_settings.setLayout(cycles_layout)

        settings_layout.addWidget(self.cycles_settings)
        # =============================================

        # Настройки для Eevee
        self.eevee_settings = QGroupBox("Настройки Eevee")

        eevee_layout = QVBoxLayout()

        eevee_samples_layout = QHBoxLayout()
        self.eevee_samples_label = QLabel("Samples:")
        self.eevee_samples_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.eevee_samples = QSpinBox()
        self.eevee_samples.setRange(1, 10000)

        eevee_samples_layout.addWidget(self.eevee_samples_label)
        eevee_samples_layout.addWidget(self.eevee_samples)
        # =============================================

        eevee_layout.addLayout(eevee_samples_layout)

        self.eevee_settings.setLayout(eevee_layout)

        settings_layout.addWidget(self.eevee_settings)
        # =============================================

        self.render_type.currentIndexChanged.connect(self.update_render_type)  # ОБРАБОТАТЬ

        self.output_folder_button.clicked.connect(self.update_output_folder)  # ОБРАБОТАТЬ

        self.render_engine.currentIndexChanged.connect(self.update_render_engine)  # ОБРАБОТАТЬ

        self.cycles_device.currentIndexChanged.connect(self.update_cycles_device)  # ОБРАБОТАТЬ
        # =============================================

        # Скрываем настройки Cycles/Eevee по умолчанию
        self.cycles_settings.setHidden(True)
        self.eevee_settings.setHidden(True)

        self.settings_window.setLayout(settings_layout)
        self.settings_window.setHidden(True)  # Скрываем по умолчанию

        # Разделитель между превью и настройками
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.preview_window)
        splitter.addWidget(self.settings_window)
        self.right_layout.addWidget(splitter)

    def update_render_type(self):
        # settings = self.file_settings.get(self.current_file)
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
            self.output_format_combobox.setCurrentIndex(self.output_format_combobox.findText(settings["File Format"]))

    def update_render_engine(self):
        # Обновляем настройки в зависимости от выбранного движка
        # settings = self.file_settings.get(self.current_file)
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

    def update_cycles_device(self):
        if self.cycles_device.currentText() == "CPU":
            self.cycles_threads_label.setHidden(False)
            self.cycles_threads.setHidden(False)
        else:
            self.cycles_threads_label.setHidden(True)
            self.cycles_threads.setHidden(True)

    def update_output_folder(self):
        # Выбор папки для сохранения результата
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения")
        if folder:
            self.output_folder.setText(folder)

    def update_blender_bin(self):
        self.current_bin = utils.transform_path_to_standard(self.blender_bin.currentText())

        if self.current_bin != "":
            self.blender_version_text.setText(self.blender_paths[self.current_bin])

        utils.set_config_value("current_bin", self.current_bin)
        utils.set_blender_in_path(self.current_bin)

    def add_blend_file(self):
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(self, "Добавить .blend файл", "", "Blender Files (*.blend);;All Files (*)")

        # projects_without_thumbnails = []

        for file_path in file_paths:
            file_path = utils.transform_path_to_standard(file_path)

            project = Project(file_path)

            item = QListWidgetItem(utils.get_file_name_from_path(project.file_path))
            item.setData(Qt.UserRole, project.unique_name)  # Сохраняем уникальный идентификатор в данных элемента
            self.blend_files_list.addItem(item)

            # project.settings = blender_api.get_settings_from_project(project.file_path)
            project.settings = self.blender_manager.get_settings_from_project(project.file_path)

            self.projects[project.unique_name] = project

            # print(project)
            # projects_without_thumbnails.append(project)

        # self.blender_manager.start_render_projects(projects_without_thumbnails, True)

    def add_blender_bin(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Добавить blender.exe файл", "", "blender.exe (*.exe)")

        file_path = utils.transform_path_to_standard(file_path)

        self.blender_paths = utils.get_blender_paths()

        # saved_paths = utils.get_blender_paths()

        if file_path not in self.blender_paths and file_path != "":

            if utils.is_blender_bin(file_path):
                self.blender_paths[file_path] = utils.get_blender_version(file_path)

                utils.set_config_value("bin_paths", self.blender_paths)

                self.blender_bin.clear()
                self.blender_bin.addItems(utils.get_blender_paths())  # Update list of blender.exe
                self.blender_bin.setCurrentIndex(-1)

            else:
                self.update_output(f"Path {file_path} not blender.exe")

        else:
            self.update_output(f"Path {file_path} already added")  # This path already in config or PATH

    def show_file_details(self, item):
        if self.current_project is not None:
            self.update_render_settings()

        # Получаем уникальный идентификатор из данных элемента
        self.current_project = self.projects[item.data(Qt.UserRole)]

        # Обновляем содержимое превью
        preview_image_path = utils.path_to_thumbnail(self.current_project.unique_name)

        if preview_image_path and QPixmap(preview_image_path).isNull() is False:
            try:
                pixmap = QPixmap(preview_image_path)
                self.preview.setPixmap(pixmap)
            except Exception as e:
                print(f"Error {str(e)}")
        else:
            self.preview.setText("Изображение не может быть загружено.")  # Очищаем превью, если изображение не доступно

        settings = self.current_project.settings

        # Допустимые форматы изменяются при выборе типа рендера
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

        # TODO: Надо обрабатывать исключение
        else:
            raise ValueError(f"Неизвестный формат файла: {settings['File Format']}. "
                             f"Ожидалось значение из 'File Formats Image' или 'File Formats Movie'.")

        self.resolution_x.setValue(settings["ResolutionX"])
        self.resolution_y.setValue(settings["ResolutionY"])
        self.resolution_scale.setValue(settings["Resolution Scale"])

        self.render_engine.setCurrentIndex(-1)
        self.render_engine.setCurrentIndex(self.render_engine.findText(settings["Render Engine"]))

        if settings["Threads"] == 0:
            self.cycles_threads.setValue(utils.get_cpu_count())
        else:
            self.cycles_threads.setValue(settings["Threads"])

        self.output_format_combobox.setCurrentIndex(-1)
        self.output_format_combobox.setCurrentIndex(self.output_format_combobox.findText(settings["File Format"]))

        self.output_folder.setText(settings["Output Path"])

        # Показываем окна превью и настроек
        self.preview_window.setHidden(False)
        self.settings_window.setHidden(False)

    def update_project_preview(self):
        self.blender_manager.render_project_thumbnail(self.current_project)

    def update_render_settings(self):
        if self.current_project is None:
            return

        settings = self.current_project.settings

        # Обновляем настройки в зависимости от изменений в интерфейсе
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
        # self.file_settings[self.current_file] = settings.copy()

        # Если устройство - CPU, обновляем количество потоков
        # if settings["Device"] == "CPU":
        #     settings["Threads"] = self.cycles_threads.value()

    def update_output(self, message):
        """Метод для обновления текста в поле прогресса."""
        self.progress_output.append(message)

    def start_render_queue(self):
        self.update_render_settings()

        # Создаем список файлов для рендера
        projects_to_render = []
        for index in range(self.blend_files_list.count()):
            item = self.blend_files_list.item(index)
            project = self.projects[item.data(Qt.UserRole)]
            projects_to_render.append(project)

        self.blender_manager.start_render_projects(projects_to_render, False)


# TODO: Проблема с utils сохраняется
# TODO: Локализации ru/en
if __name__ == "__main__":
    # Create config variables
    # sys.path.append(os.path.abspath(os.path.dirname(__file__)))  # Для работы utils

    work_directory = os.path.dirname(os.path.abspath(__file__))
    utils.set_config_value("work_directory", work_directory)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = BlenderInterface()
    window.setFixedSize(1600, 900)
    window.show()
    sys.exit(app.exec_())
