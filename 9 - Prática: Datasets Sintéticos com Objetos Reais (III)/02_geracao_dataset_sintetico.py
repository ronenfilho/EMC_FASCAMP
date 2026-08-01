"""
Script 2 - Geração Automatizada do Dataset Sintético (Nível de Chá na Caneca)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Automatizar a renderização em massa da caneca de chá, variando
    câmera (rig NURBS), rotação da caneca e cor do chá (Domain
    Randomization), distribuindo o resultado em diretórios
    `train`/`val`/`test` — Etapa 2 da especificação em
    `roteiro-pratica-claude.md`, adaptada para 4 classes (ver README:
    o roteiro original lista só 3 classes, mas o `tea_mug.fbx` e o
    relatório da prática descrevem 4 estados de líquido).

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open") e rode
        com Alt+P.
    Headless (terminal):
        blender --background --python "02_geracao_dataset_sintetico.py"

Modo de execução (ver MODO_TESTE logo abaixo):
    Por padrão roda em modo de TESTE RÁPIDO (poucas imagens por split).
    Para o dataset de produção completo (300/80/10 por classe = 1560
    imagens), troque `MODO_TESTE = False` — a saída vai para
    `/tmp/tea_dataset` em vez da pasta do projeto, para não versionar
    mais de mil imagens no git (mesma decisão da Prática 8).
"""

import math
import os
import random
import shutil
import time
from pathlib import Path

import bpy
from mathutils import Color

try:
    from importlib.util import module_from_spec, spec_from_file_location
except ImportError:  # pragma: no cover - Python sempre tem importlib
    raise


def obter_diretorio_do_script(nome_do_arquivo):
    """Descobre a pasta onde este script está salvo em disco (ver nota
    detalhada equivalente no Script 1 — mesma lógica, reaproveitada)."""
    texto = bpy.data.texts.get(nome_do_arquivo)
    if texto is not None and texto.filepath:
        caminho_real = bpy.path.abspath(texto.filepath)
        if os.path.isfile(caminho_real):
            return os.path.dirname(caminho_real)

    caminho_file = globals().get("__file__") or ""
    if caminho_file and os.path.isfile(os.path.abspath(caminho_file)):
        return os.path.dirname(os.path.abspath(caminho_file))

    return os.getcwd()


SCRIPT_DIR = obter_diretorio_do_script("02_geracao_dataset_sintetico.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")

# --------------------------------------------------------------------------
# Configuração do modo de execução (ver docstring do módulo).
# --------------------------------------------------------------------------
MODO_TESTE = True

if MODO_TESTE:
    BASE_PATH = Path(SCRIPT_DIR) / "dataset_amostra"
    RENDERS_POR_SPLIT = [("train", 3), ("val", 2), ("test", 1)]
else:
    BASE_PATH = Path("/tmp/tea_dataset")
    RENDERS_POR_SPLIT = [("train", 300), ("val", 80), ("test", 10)]

# 4 classes (não 3): o `tea_mug.fbx` traz as malhas 'Full', 'Half-Full' e
# 'Mostly-Empty'; 'empty' é a caneca sem nenhuma delas visível. Ver nota
# no README sobre a divergência com o roteiro original (que só previa 3).
CLASSES = ("empty", "mostly_empty", "half_full", "full")

NOME_MALHA_POR_CLASSE = {
    "mostly_empty": "Mostly-Empty",
    "half_full": "Half-Full",
    "full": "Full",
}


def carregar_script1():
    """Carrega o Script 1 (configuração da cena) como módulo."""
    spec = spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena(script1):
    """Monta a cena completa reaproveitando o Script 1."""
    script1.limpar_cena()
    caneca, liquidos = script1.importar_caneca()
    material_vidro, material_cha = script1.configurar_materiais_realistas()
    script1.criar_backdrop()
    script1.criar_iluminacao()
    alvo = script1.criar_alvo_da_camera(caneca)
    rig = script1.montar_rig_de_camera(alvo)
    script1.configurar_render_cycles()
    return caneca, liquidos, material_cha, rig


def isolar_classe_visivel(liquidos, classe):
    """Mostra apenas a malha de líquido correspondente à classe atual;
    para a classe 'empty', oculta todas (só a caneca de vidro vazia).
    """
    malha_alvo = NOME_MALHA_POR_CLASSE.get(classe)
    for nome_malha, objeto in liquidos.items():
        objeto.hide_render = nome_malha != malha_alvo


def randomizar_rig_de_camera(rig):
    """Sorteia um ponto aleatório no rig de câmera (elevação no arco +
    azimute na elipse). Ver nota no README: o offset precisa ser
    NEGATIVO (0 a -100) para avançar ao longo da curva — um valor
    positivo faz o Blender extrapolar para TRÁS do início da curva
    (achado ao depurar o rig; documentado em detalhe no README).
    """
    rig["circle_path_container"].constraints["Follow Path"].offset = random.uniform(0.0, -100.0)
    rig["camera_container"].constraints["Follow Path"].offset = random.uniform(0.0, -100.0)


def randomizar_rotacao_caneca(caneca):
    """Gira a caneca aleatoriamente no eixo Z, para a alça aparecer em
    posições diferentes a cada imagem."""
    caneca.rotation_euler[2] = random.uniform(0.0, 2 * math.pi)


def randomizar_cor_do_cha(material_cha, classe):
    """Varia a cor do chá (Principled BSDF + Volume Absorption) dentro de
    faixas HSV que vão do chá preto/vermelho ao chá verde. Não se aplica
    à classe 'empty' (não há líquido visível para colorir).
    """
    if classe == "empty":
        return

    nodes = material_cha.node_tree.nodes

    cor_superficie = Color()
    cor_superficie.hsv = (
        random.uniform(0.0, 0.2),
        random.uniform(0.2, 0.8),
        random.uniform(0.4, 0.7),
    )
    nodes["Principled BSDF"].inputs["Base Color"].default_value = (
        cor_superficie.r,
        cor_superficie.g,
        cor_superficie.b,
        1.0,
    )

    cor_volume = Color()
    cor_volume.hsv = (
        random.uniform(0.05, 0.15),
        random.uniform(0.6, 0.8),
        random.uniform(0.3, 0.6),
    )
    nodes["Volume Absorption"].inputs["Color"].default_value = (
        cor_volume.r,
        cor_volume.g,
        cor_volume.b,
        1.0,
    )


def preparar_diretorio_de_saida():
    """Limpa qualquer dataset anterior no BASE_PATH."""
    if BASE_PATH.exists():
        shutil.rmtree(BASE_PATH)
    BASE_PATH.mkdir(parents=True)
    print(f"[Dataset] Diretório de saída preparado: {BASE_PATH}")


def gerar_dataset(caneca, liquidos, material_cha):
    """Loop principal: para cada classe e cada split, gera N renders com
    domain randomization, salvando em `BASE_PATH/split/classe/NNNNNN.png`.
    """
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"

    rig = {
        "circle_path_container": bpy.data.objects["circle_path_container"],
        "camera_container": bpy.data.objects["camera_container"],
    }

    total_imagens = sum(qtd for _, qtd in RENDERS_POR_SPLIT) * len(CLASSES)
    imagens_geradas = 0
    tempos_de_render = []

    for classe in CLASSES:
        isolar_classe_visivel(liquidos, classe)

        for nome_split, quantidade in RENDERS_POR_SPLIT:
            diretorio_split = BASE_PATH / nome_split / classe
            diretorio_split.mkdir(parents=True, exist_ok=True)

            for indice in range(quantidade):
                randomizar_rig_de_camera(rig)
                randomizar_rotacao_caneca(caneca)
                randomizar_cor_do_cha(material_cha, classe)

                nome_arquivo = f"{str(indice).zfill(6)}.png"
                caminho_saida = diretorio_split / nome_arquivo
                scene.render.filepath = str(caminho_saida)

                inicio = time.time()
                bpy.ops.render.render(write_still=True)
                tempos_de_render.append(time.time() - inicio)

                imagens_geradas += 1
                media = sum(tempos_de_render) / len(tempos_de_render)
                restantes = total_imagens - imagens_geradas
                eta = media * restantes

                print(
                    f"[{imagens_geradas}/{total_imagens}] {nome_split}/{classe}/{nome_arquivo} "
                    f"| média={media:.2f}s/img | ETA={eta:.1f}s"
                )

    print(f"[Dataset] Concluído: {imagens_geradas} imagens em {BASE_PATH}")


def main():
    script1 = carregar_script1()
    caneca, liquidos, material_cha, rig = montar_cena(script1)

    preparar_diretorio_de_saida()
    gerar_dataset(caneca, liquidos, material_cha)


if __name__ == "__main__":
    main()
