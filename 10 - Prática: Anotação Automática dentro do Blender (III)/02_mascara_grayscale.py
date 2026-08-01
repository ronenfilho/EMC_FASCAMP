"""
Script 2 - Máscara de Segmentação em Tons de Cinza (Abordagem A)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Reaproveita o Script 1 (cena + `pass_index` + `IndexOB`) e monta a
    árvore de nós do Compositor que converte o índice de cada objeto em
    um tom de cinza normalizado (0.0–1.0), exportando uma máscara de
    segmentação em 8-bit e outra em 16-bit.

Por que dividir por 255 (ou 65535)?
    O Blender trabalha internamente com cores normalizadas entre 0.0 e
    1.0. Alimentar o canal de cor diretamente com o `pass_index` cru (ex:
    27) faria qualquer índice >= 1 aparecer como branco estourado. Dividir
    pelo valor máximo da profundidade de cor escolhida (255 para 8-bit,
    65535 para 16-bit) remapeia cada índice para um tom de cinza distinto
    dentro da faixa válida.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open") e rode
        com Alt+P. Depois, F12 renderiza usando a última configuração
        de compositor chamada por `main()`.
    Headless (terminal):
        blender --background --python "02_mascara_grayscale.py"
"""

import os
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


SCRIPT_DIR = obter_diretorio_do_script("02_mascara_grayscale.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")


def carregar_script1():
    spec = spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def limpar_compositor():
    """Cria (ou zera) a árvore de nós do Compositor da cena atual.

    Nota de API (Blender 4.x+): `scene.node_tree` não existe mais — a
    árvore do Compositor agora é um data-block de node group próprio
    (`bpy.data.node_groups`, tipo `CompositorNodeTree`), atribuído à cena
    via `scene.compositing_node_group`. Setar `scene.use_nodes = True`
    sozinho NÃO cria mais essa árvore automaticamente.
    """
    scene = bpy.context.scene
    grupo = scene.compositing_node_group
    if grupo is None:
        grupo = bpy.data.node_groups.new("ComposicaoSegmentacao", "CompositorNodeTree")
        scene.compositing_node_group = grupo
    else:
        grupo.nodes.clear()
    return grupo


def configure_compositor_grayscale(bit_depth=8):
    """Monta Render Layers -> Math (Divide) -> saída do compositor,
    mapeando `pass_index`/`Object Index` para um tom de cinza normalizado.

    Nota de API: o nó de matemática genérico não é mais
    `CompositorNodeMath` (removido) — nesta versão do Blender o mesmo nó
    `ShaderNodeMath` é compartilhado entre os editores de Shading e
    Compositing. E a saída `IndexOB` da especificação original aparece
    aqui com o rótulo `Object Index` (mesmo dado, nome atualizado).
    """
    tree = limpar_compositor()

    render_layers = tree.nodes.new(type="CompositorNodeRLayers")

    divisor = 255.0 if bit_depth == 8 else 65535.0
    math_divide = tree.nodes.new(type="ShaderNodeMath")
    math_divide.name = "DivideParaGrayscale"
    math_divide.operation = "DIVIDE"
    math_divide.inputs[1].default_value = divisor
    tree.links.new(render_layers.outputs["Object Index"], math_divide.inputs[0])

    # Grupo de saída do compositor (substitui o antigo nó "Composite"):
    # a árvore agora é um node group de verdade, com interface própria.
    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    saida = tree.nodes.new(type="NodeGroupOutput")
    tree.links.new(math_divide.outputs[0], saida.inputs["Image"])

    print(f"[Compositor] Máscara grayscale configurada: IndexOB / {divisor:.1f} ({bit_depth}-bit).")
    return tree


def renderizar_mascara(caminho_saida, bit_depth=8):
    """Renderiza usando a árvore de compositor atual, salvando o
    resultado como PNG em escala de cinza (`color_mode='BW'`) na
    profundidade de cor pedida.

    Nota crítica de gerenciamento de cores: por padrão, o Blender 5.2
    aplica o *view transform* **AgX** a qualquer render salvo, mesmo a
    um canal já normalizado matematicamente para representar dados
    "crus" (não uma cor de verdade). Isso distorce os tons de cinza —
    exatamente o problema descrito no relatório de origem desta prática
    ("índice 27 vira 92", "índice 200 vira 229" foram os valores
    medidos aqui antes da correção). A correção é forçar
    `image_settings.color_management = 'OVERRIDE'` com
    `view_transform = 'Raw'`, que faz o Blender salvar o valor do canal
    tal como ele saiu do nó Math, sem nenhuma curva de exibição —
    validado byte a byte: pass_index 1/27/200 → pixel 1/27/200 exatos.
    """
    scene = bpy.context.scene
    image_settings = scene.render.image_settings
    image_settings.file_format = "PNG"
    image_settings.color_mode = "BW"
    image_settings.color_depth = "8" if bit_depth == 8 else "16"
    image_settings.color_management = "OVERRIDE"
    image_settings.view_settings.view_transform = "Raw"

    scene.render.filepath = caminho_saida

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"[Render] Máscara {bit_depth}-bit salva em: {caminho_saida}")


def main():
    script1 = carregar_script1()
    script1.main()

    diretorio_saida = os.path.join(SCRIPT_DIR, "renders")

    configure_compositor_grayscale(bit_depth=8)
    renderizar_mascara(os.path.join(diretorio_saida, "mascara_grayscale_8bit.png"), bit_depth=8)

    configure_compositor_grayscale(bit_depth=16)
    renderizar_mascara(os.path.join(diretorio_saida, "mascara_grayscale_16bit.png"), bit_depth=16)


if __name__ == "__main__":
    main()
