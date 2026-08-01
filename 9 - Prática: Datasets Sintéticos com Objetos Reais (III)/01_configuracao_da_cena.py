"""
Script 1 - Configuração da Cena: Caneca de Vidro com Chá (Estúdio de Canto)
Blender 5.2.0 LTS | API Python (bpy + bmesh)

Objetivo didático:
    Montar, via API, a cena física completa da Prática 9: importar a
    caneca de vidro (`tea_mug.fbx`), configurar materiais realistas de
    vidro e líquido volumétrico, montar o "estúdio de canto" (backdrop
    infinito menor que o da Prática 8) e o rig de câmera baseado em
    curvas NURBS (Etapa 1).

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open", não
        colando o texto) e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01_configuracao_da_cena.py"
"""

import math
import os

import bmesh
import bpy
from mathutils import Color, Matrix, Vector

def obter_diretorio_do_script(nome_do_arquivo):
    """Descobre a pasta onde este script está salvo em disco.

    Cobre três formas de execução, em ordem de confiabilidade (lição da
    Prática 8): dentro do Blender, `__file__` NÃO é o caminho do arquivo
    — é sempre `"/" + nome_do_texto`, mesmo com o arquivo aberto do disco
    via Alt+P. Por isso `bpy.data.texts[...].filepath` é checado primeiro.
      1. Alt+P no Text Editor, arquivo aberto do disco: usa
         `bpy.data.texts[...].filepath` (validado com `os.path.isfile`).
      2. Headless (`blender --background --python arquivo.py`): usa
         `__file__`, que aqui sim é o caminho completo de verdade.
      3. Nenhuma das opções acima (ex.: conteúdo colado sem arquivo de
         origem): usa o diretório de trabalho atual como último recurso.
    """
    texto = bpy.data.texts.get(nome_do_arquivo)
    if texto is not None and texto.filepath:
        caminho_real = bpy.path.abspath(texto.filepath)
        if os.path.isfile(caminho_real):
            return os.path.dirname(caminho_real)

    caminho_file = globals().get("__file__") or ""
    if caminho_file and os.path.isfile(os.path.abspath(caminho_file)):
        return os.path.dirname(os.path.abspath(caminho_file))

    return os.getcwd()


SCRIPT_DIR = obter_diretorio_do_script("01_configuracao_da_cena.py")
FBX_PATH = os.path.join(SCRIPT_DIR, "tea_mug.fbx")

NOMES_LIQUIDO = ("Full", "Half-Full", "Mostly-Empty")
NOME_CANECA = "Glass_Mug"


def limpar_cena():
    """Remove com segurança todos os objetos e purga data-blocks órfãos."""
    for objeto in list(bpy.data.objects):
        bpy.data.objects.remove(objeto, do_unlink=True)

    for colecao in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.materials,
    ):
        for bloco in list(colecao):
            if bloco.users == 0:
                colecao.remove(bloco)


def importar_caneca():
    """Importa `tea_mug.fbx` e devolve os 4 objetos relevantes.

    O arquivo contém 4 malhas: `Glass_Mug` (a caneca de vidro) e três
    níveis de líquido (`Full`, `Half-Full`, `Mostly-Empty`) — todas
    sobrepostas na mesma origem, já apoiadas em Z=0. A "classe" vazia
    (`empty`) não tem malha própria: é simplesmente a caneca com as três
    malhas de líquido ocultas.
    """
    bpy.ops.import_scene.fbx(filepath=FBX_PATH)

    caneca = bpy.data.objects[NOME_CANECA]
    liquidos = {nome: bpy.data.objects[nome] for nome in NOMES_LIQUIDO}

    print(f"[Import] '{NOME_CANECA}' + líquidos {list(liquidos.keys())} importados de {FBX_PATH}")
    return caneca, liquidos


def configurar_materiais_realistas():
    """Ajusta os materiais `Glass` e `Tea` (vindos do FBX com Principled
    BSDF básico) para o vidro/líquido realista descrito na especificação.

    - Vidro (`Glass`): Transmission=1.0, Roughness=0.0 — transparente e
      perfeitamente liso.
    - Chá (`Tea`): mesma base de vidro (Transmission=1.0, Roughness=0.0)
      MAIS um node `Volume Absorption` ligado à entrada Volume do
      Material Output, simulando a absorção de luz pela espessura do
      líquido (fica mais escuro/saturado onde a coluna de chá é mais
      grossa) em vez de depender só da cor de superfície.
    """
    material_vidro = bpy.data.materials["Glass"]
    bsdf_vidro = material_vidro.node_tree.nodes["Principled BSDF"]
    bsdf_vidro.inputs["Transmission Weight"].default_value = 1.0
    bsdf_vidro.inputs["Roughness"].default_value = 0.0

    material_cha = bpy.data.materials["Tea"]
    bsdf_cha = material_cha.node_tree.nodes["Principled BSDF"]
    bsdf_cha.inputs["Transmission Weight"].default_value = 1.0
    bsdf_cha.inputs["Roughness"].default_value = 0.0

    nodes_cha = material_cha.node_tree.nodes
    links_cha = material_cha.node_tree.links
    saida_material = nodes_cha["Material Output"]

    volume_absorption = nodes_cha.new(type="ShaderNodeVolumeAbsorption")
    volume_absorption.location = (saida_material.location.x - 200, saida_material.location.y - 200)

    cor_cha = Color()
    cor_cha.hsv = (0.074, 0.732, 0.569)
    volume_absorption.inputs["Color"].default_value = (cor_cha.r, cor_cha.g, cor_cha.b, 1.0)
    volume_absorption.inputs["Density"].default_value = 3.4

    links_cha.new(volume_absorption.outputs["Volume"], saida_material.inputs["Volume"])

    print("[Material] 'Glass' e 'Tea' configurados (Transmission=1.0, Roughness=0.0, Volume Absorption no chá).")
    return material_vidro, material_cha


def criar_backdrop(tamanho=0.45):
    """Cria o "estúdio de canto": um cubo de `2*tamanho` metros de aresta
    com teto e duas paredes removidas — mesma técnica da Prática 8, só
    que em escala de mesa (bancada) para caber a caneca.

    A especificação sugere `tamanho=0.3`, mas nos testes visuais isso
    deixava uma pequena fresta do "vazio" visível num dos cantos do
    quadro mesmo na posição "neutra" do rig de câmera (offset=0 nas duas
    curvas). Aumentar para `0.45` dá margem suficiente sem mudar mais
    nada no rig.
    """
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    backdrop = bpy.context.active_object
    backdrop.name = "Backdrop"
    backdrop.scale = (tamanho, tamanho, tamanho)
    backdrop.location.z = tamanho

    bpy.context.view_layer.objects.active = backdrop
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(backdrop.data)
    bm.faces.ensure_lookup_table()

    faces_para_remover = []
    for face in bm.faces:
        normal = face.normal
        eh_face_superior = normal.z > 0.9
        eh_face_y_negativo = normal.y < -0.9
        eh_face_x_positivo = normal.x > 0.9
        if eh_face_superior or eh_face_y_negativo or eh_face_x_positivo:
            faces_para_remover.append(face)

    bmesh.ops.delete(bm, geom=faces_para_remover, context="FACES")
    bmesh.update_edit_mesh(backdrop.data)

    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode="OBJECT")

    print(f"[Backdrop] '{backdrop.name}' criado (aresta={2*tamanho}m) com {len(backdrop.data.polygons)} faces restantes.")
    return backdrop


def criar_iluminacao():
    """Cria a Area Light (caixa de luz difusa, 1x1m/21W) e a Sun Light
    fraca (0.03) de preenchimento, conforme a especificação.
    """
    bpy.ops.object.light_add(type="AREA", location=(0.18, -0.22, 0.32))
    area = bpy.context.active_object
    area.name = "LuzPrincipal"
    area.data.shape = "SQUARE"
    area.data.size = 1.0
    area.data.energy = 21.0
    # Rotacionada para "olhar" na direção geral do copo (canto -X/+Y).
    area.rotation_euler = (math.radians(55), 0.0, math.radians(45))

    bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, 1.0))
    sol = bpy.context.active_object
    sol.name = "LuzDePreenchimento"
    sol.data.energy = 0.03
    sol.rotation_euler = (math.radians(35), math.radians(20), 0.0)

    print("[Luz] Area Light (1x1m/21W) + Sun Light (0.03) criadas.")
    return area, sol


def criar_alvo_da_camera(caneca):
    """Cria o Empty `object_target` no centro volumétrico da caneca, e o
    torna filho (`Child Of`) de `Glass_Mug` — assim, se a caneca girar no
    eixo Z, o alvo da câmera acompanha o giro.

    O centro é calculado a partir da caixa delimitadora (bounding box) da
    própria malha da caneca, em vez de um valor fixo — continua correto
    mesmo que o modelo importado mude de tamanho/proporção no futuro.
    """
    caixa_mundo = [caneca.matrix_world @ Vector(corner) for corner in caneca.bound_box]
    centro = sum(caixa_mundo, Vector((0, 0, 0))) / 8

    bpy.ops.object.empty_add(type="CUBE", radius=0.01, location=centro)
    alvo = bpy.context.active_object
    alvo.name = "object_target"

    child_of = alvo.constraints.new(type="CHILD_OF")
    child_of.target = caneca
    child_of.inverse_matrix = caneca.matrix_world.inverted()

    print(f"[Rig] 'object_target' criado em {tuple(round(v, 4) for v in centro)} (filho de '{caneca.name}').")
    return alvo


def criar_curva_arco(alvo, raio=0.35, nome="camera_arc_path"):
    """Cria `camera_arc_path`: um quarto de círculo vertical (NURBS Path)
    indo da "visão de horizonte" (mesma altura do alvo, a `raio` metros
    de distância) até a "visão zenital" (diretamente acima do alvo).

    Construído matematicamente (em vez de arrastar vértices manualmente
    no Edit Mode) para garantir um arco geometricamente exato. A curva é
    criada no plano local XZ e depois rotacionada -45° no eixo Z, para
    que a "visão de horizonte" fique alinhada com a diagonal aberta do
    backdrop de canto (mesma direção usada no Script 1b para a câmera de
    conferência).
    """
    curva = bpy.data.curves.new(nome, type="CURVE")
    curva.dimensions = "3D"
    spline = curva.splines.new(type="NURBS")

    segmentos = 8
    spline.points.add(segmentos)  # já vem com 1 ponto; adiciona mais `segmentos`
    for indice in range(segmentos + 1):
        theta = math.radians(90 * indice / segmentos)
        x = raio * math.cos(theta)
        z = raio * math.sin(theta)
        spline.points[indice].co = (x, 0.0, z, 1.0)
    spline.use_endpoint_u = True
    spline.order_u = 3

    objeto_curva = bpy.data.objects.new(nome, curva)
    bpy.context.collection.objects.link(objeto_curva)
    objeto_curva.location = alvo.location
    objeto_curva.rotation_euler = (0.0, 0.0, math.radians(-45))

    curva.use_path = True
    curva.path_duration = 100

    print(f"[Rig] '{nome}' criado (arco de raio {raio}m, horizonte->zênite).")
    return objeto_curva


def criar_curva_elipse(ponto_inicial_mundo, raio=0.15, achatamento=0.45, nome="camera_circle_path", segmentos=16):
    """Cria `camera_circle_path`: uma elipse fechada (NURBS), posicionada
    no ponto de "horizonte" do arco. O achatamento (eixo Y menor que o
    eixo X) limita o alcance de distância da câmera ao girar lateralmente.

    Construída com os pontos de controle já no formato elíptico (em vez
    de criar um círculo e aplicar `object.scale` depois): uma escala não
    uniforme combinada com a rotação herdada via `Child Of` (mais abaixo)
    provoca cisalhamento (*shear*) na curva resultante — descoberto ao
    testar o rig e ver a câmera pular para distâncias erradas (0 a 2x o
    raio) em vez de variar suavemente entre `raio` e `raio*achatamento`.

    `raio=0.15` (bem menor que o raio do arco, 0.35) foi escolhido por
    teste visual: com um raio igual ao do arco, os pontos nas "pontas" do
    eixo maior da elipse (offset ≈0 e ≈-50, diametralmente opostos)
    empurram a câmera para muito longe ou para o lado errado do alvo,
    chegando a mostrar o "vazio" fora do backdrop (em um caso, o quadro
    inteiro ficou preto). Um raio bem menor mantém a órbita lateral como
    uma variação local em torno do ponto de horizonte, em vez de uma
    volta completa ao redor do copo — suficiente para dar variação de
    ângulo sem quebrar a regra de nunca mostrar o vazio.
    """
    curva = bpy.data.curves.new(nome, type="CURVE")
    curva.dimensions = "3D"
    spline = curva.splines.new(type="NURBS")
    spline.points.add(segmentos - 1)
    for indice in range(segmentos):
        theta = 2 * math.pi * indice / segmentos
        x = raio * math.cos(theta)
        y = raio * achatamento * math.sin(theta)
        spline.points[indice].co = (x, y, 0.0, 1.0)
    spline.use_cyclic_u = True
    spline.order_u = 3

    curva.use_path = True
    curva.path_duration = 100

    objeto_curva = bpy.data.objects.new(nome, curva)
    bpy.context.collection.objects.link(objeto_curva)
    objeto_curva.location = ponto_inicial_mundo

    print(f"[Rig] '{nome}' criado (elipse raio={raio}m, achatamento={achatamento}) em {tuple(round(v,4) for v in ponto_inicial_mundo)}.")
    return objeto_curva


def montar_rig_de_camera(alvo):
    """Monta o rig completo de câmera com curvas NURBS, seguindo a
    especificação: arco vertical (elevação) -> elipse horizontal
    achatada (azimute) -> câmera com Track To no alvo.
    """
    arco = criar_curva_arco(alvo)
    # `arco.matrix_world` só reflete a location/rotação setadas acima
    # depois de uma atualização do depsgraph — sem isso, a leitura abaixo
    # ainda veria a matriz "crua" (identidade), e `ponto_horizonte` daria
    # (0.35, 0, 0) em vez do ponto real de horizonte já deslocado/rotacionado.
    bpy.context.view_layer.update()
    ponto_horizonte = Vector(arco.matrix_world @ Vector((arco.data.splines[0].points[0].co[:3])))

    # IMPORTANTE: o Empty é criado na ORIGEM, não em `ponto_horizonte`.
    # `Follow Path` soma a posição própria do objeto (`.location`) por
    # cima do ponto calculado na curva — se já criássemos o Empty em
    # `ponto_horizonte`, o resultado ficaria duplicado/deslocado. Quem
    # posiciona o container de fato é só a constraint.
    circle_path_container = None
    bpy.ops.object.empty_add(type="CUBE", radius=0.08, location=(0, 0, 0))
    circle_path_container = bpy.context.active_object
    circle_path_container.name = "circle_path_container"

    seguir_arco = circle_path_container.constraints.new(type="FOLLOW_PATH")
    seguir_arco.name = "Follow Path"
    seguir_arco.target = arco
    # `use_curve_follow=False`: o container só translada ao longo do
    # arco, sem rotacionar. A elipse (abaixo) já cobre a variação de
    # elevação simplesmente por herdar essa translação; deixá-la sempre
    # "deitada" (nunca inclinada) evita o cisalhamento que a rotação
    # composta com a herança via Child Of provocava na órbita da câmera
    # (distâncias saltando de ~0.05 a ~0.7 em vez de variar suavemente).
    seguir_arco.use_curve_follow = False

    # Força a avaliação da constraint recém-criada antes de ler
    # `matrix_world` abaixo — sem isso, o valor ainda refletiria a
    # transformação "crua" do objeto (sem o Follow Path aplicado).
    bpy.context.view_layer.update()

    elipse = criar_curva_elipse(ponto_horizonte)
    child_of_elipse = elipse.constraints.new(type="CHILD_OF")
    child_of_elipse.name = "Child Of"
    child_of_elipse.target = circle_path_container
    child_of_elipse.inverse_matrix = circle_path_container.matrix_world.inverted()

    # Mesmo motivo do `circle_path_container`: criado na origem, a
    # constraint Follow Path é quem define a posição real.
    bpy.ops.object.empty_add(type="SPHERE", radius=0.02, location=(0, 0, 0))
    camera_container = bpy.context.active_object
    camera_container.name = "camera_container"

    seguir_elipse = camera_container.constraints.new(type="FOLLOW_PATH")
    seguir_elipse.name = "Follow Path"
    seguir_elipse.target = elipse
    seguir_elipse.use_curve_follow = True
    seguir_elipse.forward_axis = "FORWARD_X"
    seguir_elipse.up_axis = "UP_Z"

    bpy.ops.object.camera_add(location=(0, 0, 0))
    camera = bpy.context.active_object
    camera.name = "CameraDataset"
    camera.data.clip_start = 0.01
    bpy.context.scene.camera = camera

    child_of_camera = camera.constraints.new(type="CHILD_OF")
    child_of_camera.name = "Child Of"
    child_of_camera.target = camera_container
    camera.location = (0.0, 0.0, 0.0)
    camera.rotation_euler = (0.0, 0.0, 0.0)
    child_of_camera.inverse_matrix = Matrix.Identity(4)

    rastrear_alvo = camera.constraints.new(type="TRACK_TO")
    rastrear_alvo.name = "Track To"
    rastrear_alvo.target = alvo
    rastrear_alvo.track_axis = "TRACK_NEGATIVE_Z"
    rastrear_alvo.up_axis = "UP_Y"

    print("[Rig] Rig de câmera completo: arco -> elipse -> câmera (Track To no alvo).")
    return {
        "arco": arco,
        "elipse": elipse,
        "circle_path_container": circle_path_container,
        "camera_container": camera_container,
        "camera": camera,
    }


def configurar_render_cycles():
    """Configura Cycles, GPU (quando disponível) e resolução 224x224
    (mesma lógica de detecção de backend da Prática 8)."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 224
    scene.render.resolution_y = 224
    scene.cycles.samples = 128

    preferencias_cycles = bpy.context.preferences.addons["cycles"].preferences
    backends_candidatos = ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI")

    dispositivo_usado = "CPU"
    for backend in backends_candidatos:
        try:
            preferencias_cycles.compute_device_type = backend
        except TypeError:
            continue

        preferencias_cycles.get_devices()
        dispositivos_gpu = [d for d in preferencias_cycles.devices if d.type != "CPU"]
        if dispositivos_gpu:
            for dispositivo in preferencias_cycles.devices:
                dispositivo.use = dispositivo.type != "CPU"
            scene.cycles.device = "GPU"
            dispositivo_usado = f"GPU ({backend}: {dispositivos_gpu[0].name})"
            break

    print(f"[Render] Engine=Cycles | Dispositivo={dispositivo_usado} | 224x224 | samples=128")
    return dispositivo_usado


def main():
    limpar_cena()
    caneca, liquidos = importar_caneca()
    configurar_materiais_realistas()
    criar_backdrop()
    criar_iluminacao()
    alvo = criar_alvo_da_camera(caneca)
    montar_rig_de_camera(alvo)
    configurar_render_cycles()


if __name__ == "__main__":
    main()
