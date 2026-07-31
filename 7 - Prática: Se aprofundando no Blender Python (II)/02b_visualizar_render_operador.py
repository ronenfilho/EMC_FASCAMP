"""
Script 2b - Visualização das Cópias Espalhadas pelo Operador
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Complementa o Script 2 (operador customizado + properties) adicionando
    câmera e luz e renderizando o resultado em PNG, para conferência
    visual headless do espalhamento aleatório de cópias.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "02b_visualizar_render_operador.py"
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

SCRIPT2_PATH = os.path.join(SCRIPT_DIR, "02_operador_customizado_e_properties.py")


def carregar_script2():
    """Carrega o Script 2 como módulo, via caminho de arquivo."""
    spec = importlib.util.spec_from_file_location("script2_operador", SCRIPT2_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_de_estudo(script2):
    """Reaproveita o Script 2 para montar a mesma cena de estudo.

    Repete aqui (em vez de chamar `script2.main()`) apenas os passos de
    montagem de cena: registrar o operador é necessário, mas
    `unregister()` não é chamado, pelo mesmo motivo explicado no Script 2.
    """
    script2.limpar_cena()
    semente = script2.criar_objeto_semente()

    script2.register()

    bpy.context.view_layer.objects.active = semente
    semente.select_set(True)
    bpy.ops.object.espalhar_copias_aleatorias(quantidade=16, raio=3.5, semente_aleatoria=7)

    return semente


def adicionar_camera_e_luz():
    """Adiciona uma câmera ampla (mira a origem) e uma luz de área."""
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.name = "CameraVisualizacao"
    camera.rotation_euler = (1.0996, 0.0, 0.7854)  # ~63°/0°/45°, mirando a origem

    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(4, -4, 6))
    luz = bpy.context.active_object
    luz.data.energy = 800.0
    luz.data.size = 6.0

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
    script2 = carregar_script2()
    montar_cena_de_estudo(script2)
    adicionar_camera_e_luz()

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "script2_operador.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
