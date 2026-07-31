"""
Script 1 - Modificadores, Shading Suave e Materiais via Nodes
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Aprofundar o que foi visto na Prática 5 (criação/edição de malha crua)
    demonstrando a próxima camada do fluxo de trabalho do Blender via API:
    modificadores não-destrutivos, sombreamento suave e materiais
    baseados em nodes (Principled BSDF + textura procedural), temas
    centrais do vídeo "Python Crash Course for Blender" (Curtis Holt).

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01_modificadores_e_materiais.py"
"""

import bpy


def limpar_cena():
    """Remove com segurança todas as malhas, câmeras e luzes da cena atual.

    Repetimos o padrão da Prática 5: usar bpy.data em vez de bpy.ops evita
    depender de contexto de UI, o que é essencial para rodar tanto na
    interface gráfica quanto em modo headless.
    """
    tipos_para_remover = {"MESH", "CAMERA", "LIGHT"}

    for objeto in list(bpy.data.objects):
        if objeto.type in tipos_para_remover:
            bpy.data.objects.remove(objeto, do_unlink=True)

    for bloco in list(bpy.data.meshes):
        if bloco.users == 0:
            bpy.data.meshes.remove(bloco)
    for bloco in list(bpy.data.cameras):
        if bloco.users == 0:
            bpy.data.cameras.remove(bloco)
    for bloco in list(bpy.data.lights):
        if bloco.users == 0:
            bpy.data.lights.remove(bloco)


def criar_objeto_base():
    """Cria um cubo simples para servir de base aos modificadores."""
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    cubo = bpy.context.active_object
    cubo.name = "ObjetoAprofundado"
    return cubo


def adicionar_modificadores(objeto):
    """Monta uma pilha de modificadores não-destrutivos via API.

    Cada modificador é criado com `objeto.modifiers.new(nome, tipo)`, o
    equivalente programático de clicar em "Add Modifier" no painel de
    Propriedades. A ordem da pilha importa: o Bevel roda ANTES da
    Subdivision Surface, arredondando as arestas originais do cubo antes
    de a malha ser suavizada — se a ordem fosse invertida, o Bevel
    trabalharia sobre uma topologia já subdividida e o resultado seria
    bem menos previsível.
    """
    bevel = objeto.modifiers.new(name="Bisel", type="BEVEL")
    bevel.width = 0.08
    bevel.segments = 3

    subsurf = objeto.modifiers.new(name="SuperficieDeSubdivisao", type="SUBSURF")
    subsurf.levels = 2  # visualização na viewport
    subsurf.render_levels = 3  # nível usado no render final (pode ser maior)

    print(
        "[Modificadores] Pilha: "
        f"{[modificador.name for modificador in objeto.modifiers]}"
    )
    return bevel, subsurf


def suavizar_sombreamento(objeto):
    """Aplica sombreamento suave, equivalente a "Shade Smooth" no menu de
    contexto (clique direito no objeto em Object Mode).

    Nota técnica (Blender 4.1+): o antigo "Shade Smooth" simples suaviza
    TODAS as faces indiscriminadamente, o que arredonda quinas que
    deveriam continuar duras (ex.: a quina de uma mesa). Desde a
    introdução do "Shade Auto Smooth" como um modificador de Geometry
    Nodes, a forma recomendada é `shade_smooth_by_angle`, que suaviza
    apenas as faces cujo ângulo entre normais fica abaixo do limiar
    informado — quinas mais "fechadas" que isso permanecem retas.
    """
    bpy.ops.object.select_all(action="DESELECT")
    objeto.select_set(True)
    bpy.context.view_layer.objects.active = objeto

    import math

    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
    print("[Shading] Sombreamento suave aplicado (limiar de 30°).")


def criar_material_com_nodes(objeto):
    """Cria um material via node tree, o equivalente programático de abrir
    o workspace "Shading" e conectar nodes manualmente.

    Fluxo:
        1. Cria o data-block de Material. Diferente de versões antigas do
           Blender, NÃO é preciso ativar `material.use_nodes = True`: a
           partir do Blender 5.2, todo material já nasce com uma árvore
           de nodes (`node_tree`) pronta — a propriedade `use_nodes` está
           inclusive marcada como obsoleta (`DeprecationWarning`, remoção
           prevista para o Blender 6.0), pois o fluxo baseado em nodes
           deixou de ser opcional.
        2. Localiza o node "Principled BSDF" que o Blender já cria por
           padrão junto com o Material Output.
        3. Adiciona um node de textura procedural (Noise Texture) e o
           conecta à Roughness do BSDF, variando a rugosidade pela
           superfície sem depender de nenhuma imagem externa — essencial
           para o script continuar 100% autocontido e reprodutível em
           qualquer máquina.
    """
    material = bpy.data.materials.new(name="MaterialProcedural")

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.10, 0.45, 0.85, 1.0)  # azul
    bsdf.inputs["Metallic"].default_value = 0.2

    textura_ruido = nodes.new(type="ShaderNodeTexNoise")
    textura_ruido.location = (bsdf.location.x - 300, bsdf.location.y - 200)
    textura_ruido.inputs["Scale"].default_value = 8.0

    # Conecta a saída "Fac" (fator de ruído em escala de cinza) na entrada
    # Roughness do BSDF: cria variação orgânica de brilho/fosco na
    # superfície, sem precisar de nenhum arquivo de imagem.
    links.new(textura_ruido.outputs["Fac"], bsdf.inputs["Roughness"])

    objeto.data.materials.append(material)
    print(f"[Material] '{material.name}' criado e atribuído a '{objeto.name}'.")
    return material


def main():
    limpar_cena()
    objeto = criar_objeto_base()
    adicionar_modificadores(objeto)
    suavizar_sombreamento(objeto)
    criar_material_com_nodes(objeto)


if __name__ == "__main__":
    main()
