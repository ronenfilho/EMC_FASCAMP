"""
Script 2 - Geração Automatizada do Dataset Sintético (Splits train/val/test)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Automatizar a renderização em massa das letras 'A', 'B' e 'C' com
    rotação 3D e cor aleatórias (Etapa 2 da especificação em
    `instrucoes_claude_code_blender.md`), distribuindo o resultado em
    diretórios `train`/`val`/`test` prontos para treinar um classificador
    de imagens.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "02_geracao_dataset_sintetico.py"

Modo de execução (ver MODO_TESTE logo abaixo):
    Por padrão este script roda em modo de TESTE RÁPIDO (poucas imagens
    por split), como recomendado na especificação para validar o pipeline
    antes de uma renderização longa. Para gerar o dataset de produção
    completo (300/80/10 imagens por letra), troque `MODO_TESTE = False` —
    nesse caso a saída vai para `/tmp/abc_dataset` em vez da pasta local
    do projeto, para não versionar ~1170 imagens no git.
"""

import importlib.util
import math
import os
import random
import shutil
import time
from pathlib import Path

import bpy
from mathutils import Color, Euler

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


SCRIPT_DIR = obter_diretorio_do_script("02_geracao_dataset_sintetico.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")

# --------------------------------------------------------------------------
# Configuração do modo de execução (ver docstring do módulo).
# --------------------------------------------------------------------------
MODO_TESTE = True

if MODO_TESTE:
    BASE_PATH = Path(SCRIPT_DIR) / "dataset_amostra"
    OBJ_RENDERS_PER_SPLIT = [("train", 3), ("val", 2), ("test", 1)]
else:
    BASE_PATH = Path("/tmp/abc_dataset")
    OBJ_RENDERS_PER_SPLIT = [("train", 300), ("val", 80), ("test", 10)]

OBJ_NAMES = ["A", "B", "C"]


def carregar_script1():
    """Carrega o Script 1 (configuração da cena) como módulo."""
    spec = importlib.util.spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena(script1):
    """Monta a cena completa (backdrop + 3 letras + câmera + luz + render)
    reaproveitando o Script 1, e devolve as letras e o material
    compartilhado para o loop de geração.
    """
    script1.limpar_cena()
    script1.criar_backdrop()

    material = script1.criar_material_das_letras()
    letras = {nome: script1.criar_letra(nome, material) for nome in OBJ_NAMES}

    script1.criar_camera_e_luz()
    script1.configurar_render_cycles()

    return letras, material


def randomly_rotate_object(obj_to_change):
    """Aplica uma rotação euleriana aleatória (3D completa) ao objeto."""
    random_rot = (
        random.random() * 2 * math.pi,
        random.random() * 2 * math.pi,
        random.random() * 2 * math.pi,
    )
    obj_to_change.rotation_euler = Euler(random_rot, "XYZ")


def randomly_change_color(material_to_change):
    """Altera a cor base do shader Principled BSDF de forma aleatória e
    vibrante (HSV com saturação e valor fixos em 1.0, apenas o matiz
    varia) — evita tons pastéis/acinzentados que dificultam o
    aprendizado da rede neural.
    """
    color = Color()
    hue = random.random()
    color.hsv = (hue, 1.0, 1.0)

    rgba = (color.r, color.g, color.b, 1.0)
    material_to_change.node_tree.nodes["Principled BSDF"].inputs[0].default_value = rgba


def preparar_diretorio_de_saida():
    """Limpa qualquer dataset anterior no BASE_PATH, evitando misturar
    imagens de execuções de teste diferentes.
    """
    if BASE_PATH.exists():
        shutil.rmtree(BASE_PATH)
    BASE_PATH.mkdir(parents=True)
    print(f"[Dataset] Diretório de saída preparado: {BASE_PATH}")


def isolar_letra_visivel(letras, nome_visivel):
    """Garante que apenas a letra `nome_visivel` apareça no render,
    ocultando as demais via `hide_render` (mais barato que remover e
    recriar objetos a cada iteração).
    """
    for nome, letra in letras.items():
        letra.hide_render = nome != nome_visivel


def gerar_dataset(letras, material):
    """Loop principal: para cada letra e cada split, gera N renders com
    rotação e cor aleatórias, salvando em
    `BASE_PATH/split/classe/NNNNNN.png`.
    """
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"

    total_imagens = sum(quantidade for _, quantidade in OBJ_RENDERS_PER_SPLIT) * len(OBJ_NAMES)
    imagens_geradas = 0
    tempos_de_render = []

    for nome_letra in OBJ_NAMES:
        letra_atual = letras[nome_letra]
        isolar_letra_visivel(letras, nome_letra)

        for nome_split, quantidade in OBJ_RENDERS_PER_SPLIT:
            diretorio_split = BASE_PATH / nome_split / nome_letra
            diretorio_split.mkdir(parents=True, exist_ok=True)

            for indice in range(quantidade):
                randomly_rotate_object(letra_atual)
                randomly_change_color(material)

                nome_arquivo = f"{str(indice).zfill(6)}.png"
                caminho_saida = diretorio_split / nome_arquivo
                scene.render.filepath = str(caminho_saida)

                inicio = time.time()
                bpy.ops.render.render(write_still=True)
                tempos_de_render.append(time.time() - inicio)

                imagens_geradas += 1
                media_por_imagem = sum(tempos_de_render) / len(tempos_de_render)
                restantes = total_imagens - imagens_geradas
                tempo_restante_estimado = media_por_imagem * restantes

                print(
                    f"[{imagens_geradas}/{total_imagens}] {nome_split}/{nome_letra}/{nome_arquivo} "
                    f"| média={media_por_imagem:.2f}s/img "
                    f"| ETA={tempo_restante_estimado:.1f}s"
                )

    print(f"[Dataset] Concluído: {imagens_geradas} imagens em {BASE_PATH}")


def main():
    script1 = carregar_script1()
    letras, material = montar_cena(script1)

    preparar_diretorio_de_saida()
    gerar_dataset(letras, material)


if __name__ == "__main__":
    main()
