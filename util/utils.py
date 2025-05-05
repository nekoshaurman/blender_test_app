import os
import shutil
import subprocess

from managers.config_manager import config_manager


# TODO: When blender not in  PATH - program cant get utils
def transform_path_to_standard(path: str) -> str:
    return path.replace('/', '\\')


def path_to_thumbnail(project_name_in_queue):
    work_directory = config_manager.get_variable("work_directory")

    return f"{work_directory}\\thumbnails\\{project_name_in_queue}.png"


def set_config_value(key, value):
    config_manager.set_variable(key, value)


def get_config_value(key):
    return config_manager.get_variable(key)


def get_file_name_from_path(file_path):
    return os.path.basename(file_path)


def is_path_exists(file_path):
    if file_path:
        return os.path.exists(file_path)
    else:
        return None


def get_cpu_count():
    return os.cpu_count()


def set_blender_in_path(blender_path):
    # Убираем \blender.exe из пути, если он есть
    if blender_path.lower().endswith("\\blender.exe"):
        blender_path = blender_path[:-12]  # Убираем последние 12 символов ("\blender.exe")

    # Добавляем очищенный путь в переменную PATH
    os.environ["PATH"] = blender_path + os.pathsep + os.environ["PATH"]


def is_blender_bin(blender_path):
    try:
        # Попытка получить версию Blender с ограниченным временем ожидания (например, 5 секунд)
        result = subprocess.run(
            [blender_path, '--version'],
            capture_output=True,
            text=True,
            timeout=1  # Ограничиваем время ожидания до 5 секунд
        )

        # Проверяем, содержит ли вывод версию Blender
        if result.returncode == 0 and 'Blender' in result.stdout:
            print("blender.exe good")
            return True
        else:
            print("blender.exe bad")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Если команда завершилась с ошибкой, файл не найден или превышено время ожидания
        print("blender.exe bad")
        return False


def get_blender_paths():
    blender_paths = {}

    # Get paths from config
    config_paths = config_manager.get_variable("bin_paths")

    if config_paths is not None:
        for blender_path in config_paths:
            if is_path_exists(blender_path) and is_blender_bin(blender_path):
                blender_paths[blender_path] = get_blender_version(blender_path)

    # Get path from PATH
    blender_path_from_environment = shutil.which("blender")

    if is_path_exists(blender_path_from_environment) and ".EXE" in blender_path_from_environment:

        blender_path_from_environment = blender_path_from_environment.replace(".EXE", ".exe")

        if blender_path_from_environment in blender_paths:
            pass

        else:
            if is_blender_bin(blender_path_from_environment):
                blender_paths[blender_path_from_environment] = get_blender_version(blender_path_from_environment)

    return blender_paths


def get_blender_version(blender_bin_path):
    try:
        result = subprocess.run(
            [blender_bin_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5  # Ограничиваем время ожидания
        )
        # Ищем строку с версией в обоих потоках вывода
        for line in (result.stdout + result.stderr).splitlines():
            if line.startswith('Blender'):
                return line.strip()
        return "Версия не найдена"
    except Exception as e:
        return f"Ошибка: {str(e)}"
