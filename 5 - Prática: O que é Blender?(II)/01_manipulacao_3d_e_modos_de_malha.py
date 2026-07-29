"""
Script 1 - Manipulação Tridimensional e Modos de Malha
Blender 5.2.0 LTS | API Python (bpy + bmesh)

Objetivo didático:
    Demonstrar, de forma programática, os fundamentos geométricos que no
    fluxo manual do Blender são feitos via clique (Tab para alternar modos,
    seleção de vértices/arestas/faces, etc).

Como executar:
    1. Abra o Blender 5.2.0 LTS.
    2. Vá para o workspace "Scripting".
    3. Abra este arquivo e clique em "Run Script" (ou Alt+P).
    Alternativamente, via terminal (headless):
        blender --background --python "01_manipulacao_3d_e_modos_de_malha.py"
"""

import bpy
import bmesh


def limpar_cena():
    """Remove com segurança todas as malhas, câmeras e luzes da cena atual.

    Usamos bpy.data em vez de bpy.ops para evitar depender de contexto de
    UI (janela ativa, seleção etc.), o que é essencial para rodar o script
    tanto na interface gráfica quanto em modo headless.
    """
    tipos_para_remover = {"MESH", "CAMERA", "LIGHT"}

    for objeto in list(bpy.data.objects):
        if objeto.type in tipos_para_remover:
            bpy.data.objects.remove(objeto, do_unlink=True)

    # Também limpamos os data-blocks órfãos (malhas, câmeras e luzes sem
    # nenhum objeto usando-os), evitando "lixo" acumulado na cena.
    for bloco in list(bpy.data.meshes):
        if bloco.users == 0:
            bpy.data.meshes.remove(bloco)
    for bloco in list(bpy.data.cameras):
        if bloco.users == 0:
            bpy.data.cameras.remove(bloco)
    for bloco in list(bpy.data.lights):
        if bloco.users == 0:
            bpy.data.lights.remove(bloco)


def criar_cubo_de_teste():
    """Cria uma malha primitiva (cubo) para servir de objeto de estudo."""
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    cubo = bpy.context.active_object
    cubo.name = "CuboDeTeste"
    return cubo


def alternar_object_mode_edit_mode(objeto):
    """Demonstra a transição entre Object Mode e Edit Mode via API.

    - Object Mode: modo onde o objeto é manipulado como um todo (mover,
      rotacionar, escalar a malha inteira). Equivale à tecla Tab quando o
      Blender está mostrando o objeto "fechado".
    - Edit Mode: modo onde editamos a topologia interna da malha
      (vértices, arestas e faces individualmente). É o mesmo Tab, mas
      alternando para dentro da malha.

    A API expõe essa alternância via `bpy.ops.object.mode_set`, que é o
    equivalente programático de pressionar Tab com o objeto selecionado.
    """
    # Garante que o objeto de interesse está ativo e selecionado, pré-requisito
    # para que `mode_set` saiba sobre qual objeto operar.
    bpy.ops.object.select_all(action="DESELECT")
    objeto.select_set(True)
    bpy.context.view_layer.objects.active = objeto

    # Object Mode -> Edit Mode
    bpy.ops.object.mode_set(mode="EDIT")
    print(f"[Modo] '{objeto.name}' agora está em EDIT MODE.")

    # Edit Mode -> Object Mode
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"[Modo] '{objeto.name}' agora está em OBJECT MODE.")


def manipular_topologia(objeto):
    """Acessa e manipula vértices, arestas e faces via bmesh.

    O módulo `bmesh` é a forma recomendada de editar topologia via script,
    pois oferece uma representação de malha editável em memória (o mesmo
    tipo de estrutura que o Blender usa internamente quando você está em
    Edit Mode manualmente).
    """
    # Entramos em Edit Mode porque é o contexto onde bmesh.from_edit_mesh
    # espera operar (equivalente a estar "dentro" da malha, como ao
    # pressionar Tab e ver vértices/arestas/faces na viewport).
    bpy.context.view_layer.objects.active = objeto
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(objeto.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    print(f"[Topologia] Vértices: {len(bm.verts)}")
    print(f"[Topologia] Arestas:  {len(bm.edges)}")
    print(f"[Topologia] Faces:    {len(bm.faces)}")

    # Exemplo de manipulação: deslocamos o primeiro vértice no eixo Z,
    # simulando o tipo de edição feita manualmente com G, Z no teclado.
    if bm.verts:
        vertice_alvo = bm.verts[0]
        vertice_alvo.co.z += 0.5
        print(
            f"[Topologia] Vértice 0 deslocado. Nova posição: {vertice_alvo.co}"
        )

    # Grava as alterações do bmesh de volta na malha do objeto.
    bmesh.update_edit_mesh(objeto.data)

    # Retornamos ao Object Mode para deixar a cena em um estado "limpo",
    # assim como se o usuário tivesse pressionado Tab para sair da edição.
    bpy.ops.object.mode_set(mode="OBJECT")


def explicar_tris_quads_ngons():
    """Notas didáticas sobre topologia de polígonos.

    Não gera geometria nova: é um resumo conceitual, pensado para ser lido
    junto com o código acima, sobre os três tipos de faces que uma malha
    pode ter no Blender.

    - Tris (triângulos, 3 lados):
        Sempre planos (matematicamente não podem ser "empenados"), o que
        os torna previsíveis para o motor de render. São o formato final
        para o qual toda malha é convertida internamente antes do cálculo
        de iluminação/rasterização (triangulação). Porém, tris dificultam
        a modelagem orgânica e o "edge flow" para subdivisão/deformação.

    - Quads (quadriláteros, 4 lados):
        O padrão recomendado durante a modelagem. Permitem um fluxo de
        arestas (edge flow) previsível, essencial para subdivision surface,
        rigging e deformação de personagens. Cada quad é internamente
        dividido em 2 tris no momento do render, mas de forma consistente.

    - N-gons (5+ lados):
        Podem ser não-planos (os vértices não estão necessariamente no
        mesmo plano), o que causa AMBIGUIDADE na triangulação automática:
        o motor de render escolhe uma diagonal para dividir o polígono em
        triângulos, e essa escolha pode gerar sombreamento incorreto,
        artefatos visuais ("pinching") em superfícies com Subdivision
        Surface, e comportamento imprevisível ao aplicar modificadores.
        Por isso, N-gons devem ser evitados em malhas destinadas a
        deformação, render de alta qualidade ou uso em jogos/tempo real.
    """
    print(__doc__ if False else explicar_tris_quads_ngons.__doc__)


def main():
    limpar_cena()
    cubo = criar_cubo_de_teste()
    alternar_object_mode_edit_mode(cubo)
    manipular_topologia(cubo)
    explicar_tris_quads_ngons()


if __name__ == "__main__":
    main()
