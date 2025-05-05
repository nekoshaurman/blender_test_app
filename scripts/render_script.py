import bpy
import sys
import json

if __name__ == "__main__":
    file_path = sys.argv[5]
    settings = json.loads(sys.argv[6])

    print(f"Открываю файл: {file_path}")
    bpy.ops.wm.open_mainfile(filepath=file_path)

    print("Настройка параметров рендера...")
    bpy.context.scene.frame_start = settings["Frame Start"]
    bpy.context.scene.frame_end = settings["Frame End"]
    bpy.context.scene.frame_step = settings["Frame Step"]
    bpy.context.scene.frame_current = settings["Frame"]

    bpy.context.scene.render.resolution_x = settings["ResolutionX"]
    bpy.context.scene.render.resolution_y = settings["ResolutionY"]
    bpy.context.scene.render.resolution_percentage = settings["Resolution Scale"]

    bpy.context.scene.render.image_settings.file_format = settings["File Format"]

    file_name = file_path.split("\\")[-1].split(".")[0]
    bpy.context.scene.render.filepath = f'{settings["Output Path"]}/{file_name}.png'

    available_engines = ", ".join(
        engine.identifier for engine in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items
    )

    # Костыль потому что в 3.6 BLENDER_EEVEE, а в 4.2 BLENDER_EEVEE_NEXT
    if settings["Render Engine"] == "BLENDER_EEVEE":
        if "BLENDER_EEVEE_NEXT" in available_engines:
            bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
        else:
            bpy.context.scene.render.engine = "BLENDER_EEVEE"

        bpy.context.scene.eevee.taa_render_samples = settings.get("EEVEE Samples", 128)

    elif settings["Render Engine"] == "CYCLES":
        bpy.context.scene.render.engine = "CYCLES"

        bpy.context.scene.cycles.samples = settings.get("CYCLES Samples", 64)
        bpy.context.scene.cycles.use_denoising = settings.get("Denoising", True)
        bpy.context.scene.cycles.device = settings.get("Device", "GPU")

    print("Запуск рендера...")
    bpy.ops.render.render(write_still=True)
    print("Рендер завершен!")
