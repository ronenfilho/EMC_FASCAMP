"""
Script 1b - Visualização do Material e dos Modificadores via Render
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Complementa o Script 1 (modificadores, shading suave e material com
    nodes) adicionando câmera e luz e renderizando o resultado em PNG —
    a única forma confiável de "ver" o resultado quando o Blender roda em
    modo headless (--background), onde não existe viewport para
    screenshot.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01b_visualizar_render_material.py"
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

SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_modificadores_e_materiais.py")


def carregar_script1():
    """Carrega o Script 1 como módulo, via caminho de arquivo.

    `importlib.util` é necessário (em vez de `import` direto) porque o
    nome do arquivo contém espaços/acentos e não é um identificador
    Python válido.
    """
    spec = importlib.util.spec_from_file_location("script1_modificadores", SCRIPT1_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_de_estudo(script1):
    """Reaproveita o Script 1 para montar a mesma cena de estudo."""
    script1.limpar_cena()
    objeto = script1.criar_objeto_base()
    script1.adicionar_modificadores(objeto)
    script1.suavizar_sombreamento(objeto)
    script1.criar_material_com_nodes(objeto)
    return objeto


def adicionar_camera_e_luz(alvo):
    """Adiciona câmera (com 'Track To' mirando o alvo) e uma luz de área,
    escolhida por dar um realce mais suave à textura de rugosidade
    procedural do que uma luz do tipo Sun.
    """
    bpy.ops.object.camera_add(location=(4.5, -4.5, 3.2))
    camera = bpy.context.active_object
    camera.name = "CameraVisualizacao"

    restricao = camera.constraints.new(type="TRACK_TO")
    restricao.target = alvo
    restricao.track_axis = "TRACK_NEGATIVE_Z"
    restricao.up_axis = "UP_Y"

    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(3, -3, 5))
    luz = bpy.context.active_object
    luz.data.energy = 500.0
    luz.data.size = 4.0

    return camera


def escolher_motor_de_render(scene):
    """Seleciona um motor de render disponível na build atual do Blender."""
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


def renderizar_e_salvar(caminho_saida, resolucao=(960, 540)):
    """Renderiza a cena atual e salva o resultado como PNG."""
    scene = bpy.context.scene

    motor = escolher_motor_de_render(scene)
    scene.render.resolution_x = resolucao[0]
    scene.render.resolution_y = resolucao[1]
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = caminho_saida

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(write_still=True)

    print(f"[Render] Motor usado: {motor}")
    print(f"[Render] Imagem salva em: {caminho_saida}")


def abrir_imagem_automaticamente(caminho_saida):
    """Abre a imagem renderizada no visualizador padrão do macOS."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(["open", caminho_saida])
    except OSError as erro:
        print(f"[Aviso] Não foi possível abrir a imagem automaticamente: {erro}")


def main():
    script1 = carregar_script1()
    objeto = montar_cena_de_estudo(script1)
    adicionar_camera_e_luz(objeto)

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "script1_material.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
