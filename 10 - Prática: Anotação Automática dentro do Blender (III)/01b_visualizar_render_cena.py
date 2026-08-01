"""
Script 1b - Visualização da Cena de Teste (Render Normal, sem Compositor)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Reaproveita o Script 1 e renderiza a cena "normal" (imagem colorida,
    sem nenhuma árvore de compositor ligada), para conferência visual
    headless de que o Cubo, a Esfera e o Cone estão bem enquadrados antes
    de avançar para as máscaras de segmentação (Scripts 2 e 3).

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open") e rode
        com Alt+P.
    Headless (terminal):
        blender --background --python "01b_visualizar_render_cena.py"
"""

import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location

import bpy


def obter_diretorio_do_script(nome_do_arquivo):
    texto = bpy.data.texts.get(nome_do_arquivo)
    if texto is not None and texto.filepath:
        caminho_real = bpy.path.abspath(texto.filepath)
        if os.path.isfile(caminho_real):
            return os.path.dirname(caminho_real)

    caminho_file = globals().get("__file__") or ""
    if caminho_file and os.path.isfile(os.path.abspath(caminho_file)):
        return os.path.dirname(os.path.abspath(caminho_file))

    return os.getcwd()


SCRIPT_DIR = obter_diretorio_do_script("01b_visualizar_render_cena.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")


def carregar_script1():
    spec = spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def renderizar_e_salvar(caminho_saida):
    scene = bpy.context.scene
    scene.use_nodes = False  # garante que nenhuma árvore de compositor interfira neste render "normal"
    scene.render.filepath = caminho_saida

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"[Render] Imagem salva em: {caminho_saida}")


def abrir_imagem_automaticamente(caminho_saida):
    if sys.platform != "darwin":
        return
    try:
        subprocess.Popen(["open", caminho_saida])
    except OSError as erro:
        print(f"[Aviso] Não foi possível abrir a imagem automaticamente: {erro}")


def main():
    script1 = carregar_script1()
    script1.main()

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "cena_normal.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
