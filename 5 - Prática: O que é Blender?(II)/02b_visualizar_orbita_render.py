"""
Script 2b - Visualização da Órbita via Render de Animação (vídeo)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Reaproveita o rig de câmera do Script 2 e renderiza a animação
    completa (frames 1-100) como um vídeo MP4, permitindo "ver" a órbita
    funcionando mesmo em modo headless, sem precisar abrir a interface.

Como executar:
    Headless (terminal):
        blender --background --python "02b_visualizar_orbita_render.py"
"""

import bpy
import os
import sys
import subprocess
import importlib.util

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

SCRIPT2_PATH = os.path.join(SCRIPT_DIR, "02_rigging_de_camera_com_constraints.py")


def carregar_script2():
    """Carrega o Script 2 como módulo via caminho de arquivo.

    Requer rodar este script a partir do terminal (`blender --python
    02b_....py`) ou abrir o arquivo do disco no Blender (File > Open) —
    se o código for colado num bloco de texto novo, não há como localizar
    o Script 2 automaticamente.
    """
    spec = importlib.util.spec_from_file_location("script2_rig", SCRIPT2_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_com_rig(script2):
    """Reaproveita todas as etapas do Script 2 para montar a cena."""
    script2.limpar_cena()
    alvo = script2.criar_objeto_alvo()
    empty_foco = script2.criar_empty_de_foco(alvo)
    trilho = script2.criar_trilho_circular(alvo)
    container = script2.criar_container_da_camera(trilho)
    camera = script2.criar_camera_com_rig(empty_foco, container)
    script2.animar_orbita_da_camera(container)
    return alvo, camera


def adicionar_luz():
    """O Script 2 não inclui iluminação (não é o foco dele); adicionamos
    uma luz simples aqui só para o objeto aparecer no render."""
    bpy.ops.object.light_add(type="SUN", location=(4, -4, 6))
    luz = bpy.context.active_object
    luz.data.energy = 3.0
    return luz


def escolher_motor_de_render(scene):
    candidatos = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES")
    disponiveis = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }
    for candidato in candidatos:
        if candidato in disponiveis:
            scene.render.engine = candidato
            return candidato
    return scene.render.engine


def renderizar_video_da_orbita(caminho_saida, resolucao=(640, 360), passo_de_frame=2):
    """Renderiza a animação inteira (frame_start..frame_end) como MP4."""
    scene = bpy.context.scene

    motor = escolher_motor_de_render(scene)
    scene.render.resolution_x = resolucao[0]
    scene.render.resolution_y = resolucao[1]
    scene.frame_step = passo_de_frame

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.filepath = caminho_saida

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(animation=True)

    print(f"[Render] Motor usado: {motor}")
    print(f"[Render] Vídeo salvo em: {caminho_saida}")


def abrir_video_automaticamente(caminho_saida):
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(["open", caminho_saida])
    except OSError as erro:
        print(f"[Aviso] Não foi possível abrir o vídeo automaticamente: {erro}")


def main():
    script2 = carregar_script2()
    montar_cena_com_rig(script2)
    adicionar_luz()

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "script2_orbita.mp4")
    renderizar_video_da_orbita(caminho_saida)
    abrir_video_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
