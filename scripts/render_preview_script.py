import os
import sys
import bpy
import traceback

# sys.path.append(os.path.abspath(os.path.dirname(__file__)))
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

import util.utils as utils

if __name__ == "__main__":
    try:
        # Получаем параметры из аргументов командной строки
        file_path = sys.argv[5]
        unique_name = sys.argv[6]

        # work_directory = config_manager.get_variable("work_directory")
        work_directory = utils.get_config_value("work_directory")

        if not work_directory:
            raise ValueError("Не задана рабочая директория (work_directory)")

        # Генерация пути к миниатюре
        result_thumbnail_path = utils.path_to_thumbnail(unique_name)

        # Открываем файл в Blender
        print(f"Открываю файл: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл '{file_path}' не найден")
        bpy.ops.wm.open_mainfile(filepath=file_path)

        # Настройка параметров рендера
        print(f"Настройка параметров рендера миниатюры {unique_name}...")
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = result_thumbnail_path

        # Изменяем размер изображения
        if bpy.context.scene.render.resolution_x >= bpy.context.scene.render.resolution_y:
            percentage = 100 * round(512 / bpy.context.scene.render.resolution_x, 2)
        else:
            percentage = 100 * round(288 / bpy.context.scene.render.resolution_y, 2)

        bpy.context.scene.render.resolution_percentage = int(percentage)

        # Настройка движка рендера
        render_engine = bpy.context.scene.render.engine
        if render_engine == 'CYCLES':
            bpy.context.scene.cycles.samples = 16
        elif render_engine == 'BLENDER_EEVEE' or render_engine == 'BLENDER_EEVEE_NEXT':
            bpy.context.scene.eevee.taa_render_samples = 16
        else:
            raise ValueError(f"Неподдерживаемый движок рендера: {render_engine}")

        # Рендеринг миниатюры
        print(f"Запуск рендера миниатюры {unique_name}...")
        bpy.ops.render.render(write_still=True)
        print(f"Рендер миниатюры {unique_name} завершен!")

    except FileNotFoundError as e:
        # Обработка ошибки, если файл не найден
        print(f"Ошибка: Файл не найден - {e}")
        sys.exit(1)  # Выход с кодом ошибки

    except ValueError as e:
        # Обработка ошибки, если данные некорректны
        print(f"Ошибка: Некорректные данные - {e}")
        sys.exit(1)

    except AttributeError as e:
        # Обработка ошибки, если атрибут не существует
        print(f"Ошибка: Атрибут не найден - {e}")
        sys.exit(1)

    except RuntimeError as e:
        # Обработка ошибки во время выполнения Blender
        print(f"Ошибка: Проблема с Blender - {e}")
        sys.exit(1)

    except Exception as e:
        # Обработка всех остальных исключений
        print(f"Неизвестная ошибка: {e}")
        traceback.print_exc()  # Вывод полного трейса ошибки
        sys.exit(1)
