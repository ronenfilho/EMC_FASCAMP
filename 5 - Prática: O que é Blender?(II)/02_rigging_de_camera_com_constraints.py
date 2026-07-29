"""
Script 2 - Rigging de Câmera com Restrições (Camera Constraints)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Automatizar o sistema mecânico de câmera orbital (trilho circular +
    mira automática no alvo), replicando via API o fluxo manual de
    rigging de câmera com constraints.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "02_rigging_de_camera_com_constraints.py"
"""

import bpy
from mathutils import Matrix


def limpar_cena():
    """Remove com segurança todas as malhas, câmeras e luzes da cena atual.

    Duplicada aqui (em vez de importada do Script 1) de propósito: este
    script precisa funcionar tanto rodando via terminal quanto colado
    diretamente no workspace "Scripting" do Blender, e nesse segundo
    caso não há um caminho de arquivo confiável para localizar o Script 1
    no disco.
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


def criar_objeto_alvo():
    """Cria a malha central que servirá de alvo do rig de câmera."""
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    alvo = bpy.context.active_object
    alvo.name = "ObjetoAlvo"
    return alvo


def criar_empty_de_foco(alvo):
    """Cria o Empty 'track_to_empty' na altura focal exata do alvo.

    Esse Empty fica parado: ele só marca o ponto para onde a câmera deve
    olhar, desacoplando "o que mirar" (Track To -> este Empty) de "onde a
    câmera está fisicamente" (Follow Path -> trilho circular).
    """
    altura_focal = alvo.location.z + (alvo.dimensions.z / 2)
    bpy.ops.object.empty_add(
        type="CUBE",
        location=(alvo.location.x, alvo.location.y, altura_focal),
    )
    empty_foco = bpy.context.active_object
    empty_foco.name = "track_to_empty"
    return empty_foco


def criar_trilho_circular(alvo, raio=6.0):
    """Cria o trilho circular 'CameraPath' ao redor do alvo.

    Nota didática: a restrição usada mais adiante se chama "Follow Path",
    mas isso não exige a primitiva literal "NURBS Path" (que é uma curva
    ABERTA, em linha reta). Para uma órbita fechada de 360°, é necessária
    uma curva NURBS *circular e fechada* — por isso usamos
    `primitive_nurbs_circle_add`, mantendo o nome 'CameraPath' pedido.
    """
    bpy.ops.curve.primitive_nurbs_circle_add(
        radius=raio,
        location=(alvo.location.x, alvo.location.y, alvo.location.z),
    )
    trilho = bpy.context.active_object
    trilho.name = "CameraPath"

    # path_duration = 100 define a escala usada pela restrição Follow
    # Path: um offset de -100 (ver animar_orbita_da_camera) corresponde a
    # exatamente UMA volta completa no trilho.
    trilho.data.use_path = True
    trilho.data.path_duration = 100

    return trilho


def criar_container_da_camera(trilho):
    """Cria o Empty pequeno 'camera_container' que desliza sobre o trilho."""
    bpy.ops.object.empty_add(type="PLAIN_AXES", radius=0.2, location=(0, 0, 0))
    container = bpy.context.active_object
    container.name = "camera_container"

    restricao_follow = container.constraints.new(type="FOLLOW_PATH")
    restricao_follow.name = "Follow Path"
    restricao_follow.target = trilho
    restricao_follow.use_fixed_location = False  # offset em "frames", não em 0-1

    return container


def criar_camera_com_rig(empty_foco, container):
    """Cria a Câmera e monta a pilha de constraints na ORDEM CORRETA.

    Fluxo intencional (replicando o processo manual do tutorial):
      1. Cria a câmera e aplica "Track To" -> ela passa a mirar o alvo.
      2. Só depois aplica "Child Of" -> ela passa a herdar a posição do
         'camera_container' (que desliza no trilho). Como foi adicionada
         por último, "Child Of" cai no FIM da pilha por padrão.
      3. Constraints são avaliadas de cima para baixo. Se "Child Of"
         ficasse no fim, a câmera seria primeiro apontada (Track To) e só
         DEPOIS reposicionada (Child Of) — a posição correta chegaria
         tarde demais e a mira ficaria incorreta. Por isso movemos
         "Child Of" para o topo (índice 0) da pilha.
      4. Por fim, zeramos a localização/rotação LOCAL da câmera e a
         `inverse_matrix` da constraint "Child Of". Sem isso, a câmera
         "escapa" do trilho por dois motivos combinados:
         - qualquer localização própria da câmera seria SOMADA à posição
           herdada do container;
         - a API do Blender captura automaticamente, no momento da
           criação da constraint, uma `inverse_matrix` igual à posição
           ATUAL do container no trilho (para simular o comportamento
           padrão de "parentar sem pular de lugar"). Como o container já
           estava posicionado em algum ponto do círculo nesse instante,
           essa matriz embutiria um deslocamento fixo (do tamanho do
           raio do trilho) em todos os frames seguintes. Zerá-la garante
           que a câmera acompanhe o container em qualquer ponto do
           trilho, exatamente como pedido no enunciado.
    """
    bpy.ops.object.camera_add(location=(0, 0, 0))
    camera = bpy.context.active_object
    camera.name = "CameraOrbital"

    # 1) Track To -> aponta para o Empty de foco.
    track_to = camera.constraints.new(type="TRACK_TO")
    track_to.name = "Track To"
    track_to.target = empty_foco
    track_to.track_axis = "TRACK_NEGATIVE_Z"
    track_to.up_axis = "UP_Y"

    # 2) Child Of -> a câmera passa a ser filha do container.
    child_of = camera.constraints.new(type="CHILD_OF")
    child_of.name = "Child Of"
    child_of.target = container

    # 3) Move "Child Of" para o topo (índice 0) da pilha de constraints.
    indice_child_of = camera.constraints.find("Child Of")
    camera.constraints.move(indice_child_of, 0)

    # 4) Zera a transformação local da câmera E a inverse_matrix da
    # constraint (ver explicação detalhada no docstring desta função).
    camera.location = (0.0, 0.0, 0.0)
    camera.rotation_euler = (0.0, 0.0, 0.0)
    child_of.inverse_matrix = Matrix.Identity(4)

    bpy.context.scene.camera = camera
    return camera


def animar_orbita_da_camera(container, frame_inicial=1, frame_final=100):
    """Anima o offset do 'Follow Path' do container: 0 -> -100.

    Como o trilho foi configurado com `path_duration = 100`, um offset de
    -100 equivale a exatamente uma volta completa (360°) ao redor do
    alvo. O sinal negativo apenas define o sentido do percurso.
    """
    restricao_follow = container.constraints["Follow Path"]
    caminho_do_dado = 'constraints["Follow Path"].offset'

    restricao_follow.offset = 0
    restricao_follow.keyframe_insert(data_path="offset", frame=frame_inicial)

    restricao_follow.offset = -100
    restricao_follow.keyframe_insert(data_path="offset", frame=frame_final)

    # Interpolação linear = velocidade constante ao longo da órbita
    # (evita o "ease in/out" padrão do Blender, que faria a câmera
    # acelerar e desacelerar de forma não uniforme).
    #
    # Desde o Blender 4.4, Actions passaram a usar um sistema "layered"
    # (Action Slots), então `action.fcurves` deixou de existir
    # diretamente. `fcurve_ensure_for_datablock` é o acessor recomendado:
    # ele localiza (ou cria) a fcurve certa independentemente da versão
    # interna da Action.
    action = container.animation_data.action
    if action is not None:
        fcurve = action.fcurve_ensure_for_datablock(container, caminho_do_dado)
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = "LINEAR"

    bpy.context.scene.frame_start = frame_inicial
    bpy.context.scene.frame_end = frame_final


def main():
    limpar_cena()

    alvo = criar_objeto_alvo()
    empty_foco = criar_empty_de_foco(alvo)
    trilho = criar_trilho_circular(alvo)
    container = criar_container_da_camera(trilho)
    camera = criar_camera_com_rig(empty_foco, container)
    animar_orbita_da_camera(container)

    nomes_constraints = [c.name for c in camera.constraints]
    print(f"[Rig] Pilha de constraints da câmera (ordem de avaliação): {nomes_constraints}")
    print("[Rig] Esperado: ['Child Of', 'Track To']")


if __name__ == "__main__":
    main()
