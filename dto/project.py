import os
import random

from util import utils


class Project:
    def __init__(self, file_path):
        self.file_path = file_path
        self.unique_name = self.generate_unique_name()
        self.preview_path = self.get_thumbnail_path()
        self.settings = {}

    def generate_unique_name(self):
        base_name = os.path.basename(self.file_path)  # Получаем имя файла без пути

        return f"{base_name}_{random.randint(1000, 9999)}"

    def get_thumbnail_path(self):
        return utils.path_to_thumbnail(self.unique_name)

    def set_settings(self, new_settings):
        self.settings = new_settings

    def __repr__(self):
        return f"Project(name={self.unique_name}, unique_name={self.unique_name}, file_path={self.file_path})"
