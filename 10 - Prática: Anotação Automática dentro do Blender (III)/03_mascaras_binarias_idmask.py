"""
Script 3 - Máscaras Binárias Individuais via ID Mask (Abordagem B)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Reaproveita o Script 1 e monta, para cada objeto de interesse (Cubo,
    Esfera, Cone), um nó `ID Mask` isolando exatamente os pixels daquele
    `pass_index`, produzindo uma máscara estritamente preto-e-branco
    (sem suavização/anti-aliasing), diferente da rampa de cinza contínua
    do Script 2.

Diferença para o Script 2 (grayscale):
    A Abordagem A (grayscale) gera UMA imagem com vários tons de cinza
    (um por objeto). A Abordagem B (ID Mask) gera uma imagem BINÁRIA
    (só preto e branco) PARA CADA objeto — útil quando o objetivo é
    treinar um modelo por classe ou quando o anti-aliasing entre tons de
    cinza próximos poderia confundir a segmentação.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open") e rode
        com Alt+P.
    Headless (terminal):
        blender --background --python "03_mascaras_binarias_idmask.py"
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


SCRIPT_DIR = obter_diretorio_do_script("03_mascaras_binarias_idmask.py")
SCRIPT1_PATH = os.path.join(SCRIPT_DIR, "01_configuracao_da_cena.py")


def carregar_script1():
    spec = spec_from_file_location("script1_cena", SCRIPT1_PATH)
    modulo = module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def limpar_compositor():
    """Mesma lógica do Script 2: a árvore do Compositor é um node group
    próprio (`scene.compositing_node_group`), não mais `scene.node_tree`.
    """
    scene = bpy.context.scene
    grupo = scene.compositing_node_group
    if grupo is None:
        grupo = bpy.data.node_groups.new("ComposicaoSegmentacao", "CompositorNodeTree")
        scene.compositing_node_group = grupo
    else:
        grupo.nodes.clear()
    return grupo


def configure_compositor_binary_masks(objetos_e_indices):
    """Monta um nó `ID Mask` por objeto, todos lendo do mesmo Render
    Layers, mais o Group Output (saída do compositor) pronto para
    receber a ligação de qual máscara será renderizada em cada passo.

    Nota de API: o nó `ID Mask` nesta versão do Blender NÃO tem mais o
    índice como propriedade fixa do nó — agora `Index` e `Anti-Alias`
    são ENTRADAS (sockets) do próprio nó, ajustáveis via
    `node.inputs['Index'].default_value`. `Anti-Alias = False` é o que
    garante a máscara estritamente binária (sem pixels intermediários
    nas bordas do objeto).
    """
    tree = limpar_compositor()

    render_layers = tree.nodes.new(type="CompositorNodeRLayers")

    tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    saida = tree.nodes.new(type="NodeGroupOutput")

    nos_id_mask = {}
    for nome, indice in objetos_e_indices.items():
        id_mask = tree.nodes.new(type="CompositorNodeIDMask")
        id_mask.name = f"IDMask_{nome}"
        id_mask.label = f"ID Mask - {nome} (index={indice})"
        id_mask.inputs["Index"].default_value = indice
        id_mask.inputs["Anti-Alias"].default_value = False
        tree.links.new(render_layers.outputs["Object Index"], id_mask.inputs["ID value"])
        nos_id_mask[nome] = id_mask
        print(f"[Compositor] ID Mask criado para '{nome}' (index={indice}, anti-alias=False).")

    return tree, saida, nos_id_mask


def renderizar_mascara_binaria(tree, saida, no_id_mask, caminho_saida):
    """Liga a saída Alpha do `ID Mask` escolhido ao Group Output e
    renderiza uma máscara binária (8-bit, preto e branco puro).
    """
    tree.links.new(no_id_mask.outputs["Alpha"], saida.inputs["Image"])

    scene = bpy.context.scene
    image_settings = scene.render.image_settings
    image_settings.file_format = "PNG"
    image_settings.color_mode = "BW"
    image_settings.color_depth = "8"
    # Mesma correção de gerenciamento de cores do Script 2: sem isso, o
    # AgX distorceria até uma máscara binária (1.0 deixaria de ser branco
    # puro / 0.0 deixaria de ser preto puro em alguns casos de mistura
    # nas bordas antialiased do restante do render).
    image_settings.color_management = "OVERRIDE"
    image_settings.view_settings.view_transform = "Raw"

    scene.render.filepath = caminho_saida
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    print(f"[Render] Máscara binária salva em: {caminho_saida}")


def main():
    script1 = carregar_script1()
    script1.main()

    tree, saida, nos_id_mask = configure_compositor_binary_masks(script1.OBJETOS_E_INDICES)

    diretorio_saida = os.path.join(SCRIPT_DIR, "renders")
    nomes_arquivo = {
        "Cubo": "seg_cubo.png",
        "Esfera": "seg_esfera.png",
        "Cone": "seg_cone.png",
    }

    for nome, no_id_mask_atual in nos_id_mask.items():
        caminho_saida = os.path.join(diretorio_saida, nomes_arquivo[nome])
        renderizar_mascara_binaria(tree, saida, no_id_mask_atual, caminho_saida)


if __name__ == "__main__":
    main()
