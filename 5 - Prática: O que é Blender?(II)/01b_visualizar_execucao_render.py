"""
Script 1b - Visualização da Execução via Render Automático
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Complementa o Script 1 (manipulação 3D e modos de malha) adicionando
    câmera, luz e uma renderização automática salva em PNG. Isso resolve o
    problema de "visualizar" o resultado quando o Blender roda em modo
    headless (--background), onde não existe janela/viewport para se
    tirar um screenshot.

Por que renderizar em vez de usar screenshot de viewport?
    `bpy.ops.screen.screenshot` depende de uma área de tela (viewport)
    real e ativa — ela falha em modo --background. Já
    `bpy.ops.render.render(write_still=True)` funciona em qualquer
    contexto, com ou sem interface gráfica, por isso é a forma correta
    e escalável de "ver" o resultado de um pipeline automatizado.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01b_visualizar_execucao_render.py"
"""

import bpy
import os
import sys
import subprocess
import importlib.util

# Diretório onde este script está salvo. Em execução via `--python <path>`
# ou Alt+P (Blender define __file__ nesses casos) conseguimos localizar o
# Script 1 ao lado para reaproveitar suas funções sem duplicar código.
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()

SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_manipulacao_3d_e_modos_de_malha.py")


def carregar_script1():
    """Carrega o Script 1 como módulo, via caminho de arquivo.

    Usamos `importlib.util` (em vez de `import`) porque o nome do arquivo
    contém espaços/acentos e não é um identificador Python válido para
    um `import` normal.
    """
    spec = importlib.util.spec_from_file_location("script1_mesh", SCRIPT1_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_de_estudo(script1):
    """Reaproveita o Script 1 para montar a mesma cena de estudo."""
    script1.limpar_cena()
    cubo = script1.criar_cubo_de_teste()
    script1.alternar_object_mode_edit_mode(cubo)
    script1.manipular_topologia(cubo)
    return cubo


def adicionar_camera_e_luz(alvo):
    """Adiciona câmera e luz apontando para o objeto de estudo.

    A câmera usa uma restrição 'Track To' para sempre mirar no alvo,
    independentemente de onde ela seja posicionada — o mesmo mecanismo
    que será aprofundado no Script 2 (rigging de câmera).
    """
    bpy.ops.object.camera_add(location=(4, -4, 3))
    camera = bpy.context.active_object
    camera.name = "CameraVisualizacao"

    restricao = camera.constraints.new(type="TRACK_TO")
    restricao.target = alvo
    restricao.track_axis = "TRACK_NEGATIVE_Z"
    restricao.up_axis = "UP_Y"

    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="SUN", location=(4, -4, 6))
    luz = bpy.context.active_object
    luz.data.energy = 3.0

    return camera


def escolher_motor_de_render(scene):
    """Seleciona um motor de render disponível na build atual do Blender.

    Diferentes versões/branches do Blender podem expor identificadores
    ligeiramente diferentes para o Eevee (ex: 'BLENDER_EEVEE_NEXT').
    Consultamos os identificadores válidos em tempo de execução para não
    quebrar o script por causa de um nome fixo.
    """
    candidatos = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES")
    disponiveis = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }

    for candidato in candidatos:
        if candidato in disponiveis:
            scene.render.engine = candidato
            return candidato

    # Se nada da lista bater, mantém o motor padrão já configurado na cena.
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
    """Abre a imagem renderizada no visualizador padrão do macOS.

    Útil justamente para os casos headless: mesmo sem a interface do
    Blender, o resultado aparece na tela via o app Preview do macOS.
    """
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(["open", caminho_saida])
    except OSError as erro:
        print(f"[Aviso] Não foi possível abrir a imagem automaticamente: {erro}")


def main():
    script1 = carregar_script1()
    cubo = montar_cena_de_estudo(script1)
    adicionar_camera_e_luz(cubo)

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "script1_visualizacao.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
