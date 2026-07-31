"""
Script 1b - Visualização do Estúdio Fotográfico via Render
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Complementa o Script 1 renderizando a cena montada (backdrop + letra
    'A' visível) para conferência visual headless do enquadramento de
    câmera, iluminação e do backdrop com as faces removidas.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01b_visualizar_render_estudio.py"
"""

import importlib.util
import os
import subprocess
import sys

import bpy

def obter_diretorio_do_script(nome_do_arquivo):
    """Descobre a pasta onde este script está salvo em disco.

    Cobre três formas de execução:
      1. Headless (`blender --background --python arquivo.py`): `__file__`
         vem preenchido normalmente com o caminho completo.
      2. Alt+P no Text Editor do Blender: mesmo com o arquivo aberto do
         disco, `__file__` costuma vir como string vazia (quirk do
         Blender) em vez de lançar `NameError` — nesse caso usamos
         `bpy.data.texts[...].filepath`, que é o caminho real do arquivo.
      3. Nenhuma das opções acima disponível: usa o diretório de trabalho
         atual como último recurso.
    """
    caminho_file = globals().get("__file__") or ""
    if caminho_file:
        return os.path.dirname(os.path.abspath(caminho_file))

    texto = bpy.data.texts.get(nome_do_arquivo)
    if texto is not None and texto.filepath:
        return os.path.dirname(bpy.path.abspath(texto.filepath))

    return os.getcwd()


SCRIPT_DIR = obter_diretorio_do_script("01b_visualizar_render_estudio.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")


def carregar_script1():
    """Carrega o Script 1 como módulo, via caminho de arquivo."""
    spec = importlib.util.spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena_de_estudo(script1):
    """Reaproveita o Script 1 e deixa só a letra 'A' visível no render,
    exatamente como o Script 2 fará durante a geração do dataset.
    """
    script1.limpar_cena()
    script1.criar_backdrop()

    material = script1.criar_material_das_letras()
    letras = {nome: script1.criar_letra(nome, material) for nome in ("A", "B", "C")}

    script1.criar_camera_e_luz()
    script1.configurar_render_cycles()

    for nome, letra in letras.items():
        letra.hide_render = nome != "A"

    return letras


def renderizar_e_salvar(caminho_saida):
    """Renderiza a cena atual (já configurada em 224x224/Cycles pelo
    Script 1) e salva o resultado como PNG.
    """
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = caminho_saida

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(write_still=True)

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
    montar_cena_de_estudo(script1)

    caminho_saida = os.path.join(SCRIPT_DIR, "renders", "estudio_letra_A.png")
    renderizar_e_salvar(caminho_saida)
    abrir_imagem_automaticamente(caminho_saida)


if __name__ == "__main__":
    main()
