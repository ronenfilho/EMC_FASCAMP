"""
Script 1b - Visualização do Estúdio de Canto via Render
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Complementa o Script 1 renderizando a cena montada (caneca cheia de
    chá, rig de câmera no ponto de "horizonte") para conferência visual
    headless dos materiais de vidro/chá, do backdrop de canto e do
    enquadramento inicial da câmera.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open") e rode
        com Alt+P.
    Headless (terminal):
        blender --background --python "01b_visualizar_render_estudio.py"
"""

import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location

import bpy


def obter_diretorio_do_script(nome_do_arquivo):
    """Descobre a pasta onde este script está salvo em disco (mesma
    lógica documentada em detalhe no Script 1)."""
    texto = bpy.data.texts.get(nome_do_arquivo)
    if texto is not None and texto.filepath:
        caminho_real = bpy.path.abspath(texto.filepath)
        if os.path.isfile(caminho_real):
            return os.path.dirname(caminho_real)

    caminho_file = globals().get("__file__") or ""
    if caminho_file and os.path.isfile(os.path.abspath(caminho_file)):
        return os.path.dirname(os.path.abspath(caminho_file))

    return os.getcwd()


SCRIPT_DIR = obter_diretorio_do_script("01b_visualizar_render_estudio.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")


def carregar_script1():
    spec = spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_de_estudo(script1):
    """Reaproveita o Script 1 e deixa a caneca cheia ('Full') visível,
    com a câmera no ponto inicial do rig (offset=0 em ambas as curvas).
    """
    script1.limpar_cena()
    caneca, liquidos = script1.importar_caneca()
    script1.configurar_materiais_realistas()
    script1.criar_backdrop()
    script1.criar_iluminacao()
    alvo = script1.criar_alvo_da_camera(caneca)
    script1.montar_rig_de_camera(alvo)
    script1.configurar_render_cycles()

    for nome, objeto in liquidos.items():
        objeto.hide_render = nome != "Full"

    return caneca, liquidos


def renderizar_e_salvar(caminho_saida):
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
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
    montar_cena_de_estudo(script1)

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "estudio_caneca_cheia.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
