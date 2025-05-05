import json
import os


class ConfigManager:
    def __init__(self, file_path="config.json"):
        self.file_path = file_path
        # Загрузка существующих данных из файла при инициализации
        self._variables = self._load_config()

    def _load_config(self):
        """Загрузка данных из JSON-файла"""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """Сохранение данных в JSON-файл"""
        with open(self.file_path, "w") as f:
            json.dump(self._variables, f, indent=4)

    def set_variable(self, key, value):
        self._variables[key] = value
        print(f"Переменная '{key}' установлена на значение: {value}")
        self._save_config()  # Сохраняем изменения в файл

    def get_variable(self, key):
        return self._variables.get(key)

    def has_variable(self, key):
        return key in self._variables


# Создаем единственный экземпляр Config
config_manager = ConfigManager()
