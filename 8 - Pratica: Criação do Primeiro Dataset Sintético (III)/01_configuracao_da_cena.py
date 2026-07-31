"""
Script 1 - Configuração da Cena: Estúdio Fotográfico + Letras 3D
Blender 5.2.0 LTS | API Python (bpy + bmesh)

Objetivo didático:
    Montar, via API, o "estúdio fotográfico" (backdrop infinito) e as três
    letras 3D ('A', 'B', 'C') que servirão de base para a geração do
    dataset sintético do Script 2 — Etapa 1 da especificação em
    `instrucoes_claude_code_blender.md`.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01_configuracao_da_cena.py"
"""

import math

import bmesh
import bpy


def limpar_cena():
    """Remove com segurança todas as malhas, textos, câmeras e luzes."""
    tipos_para_remover = {"MESH", "FONT", "CAMERA", "LIGHT"}

    for objeto in list(bpy.data.objects):
        if objeto.type in tipos_para_remover:
            bpy.data.objects.remove(objeto, do_unlink=True)

    for colecao in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for bloco in list(colecao):
            if bloco.users == 0:
                colecao.remove(bloco)


def criar_backdrop():
    """Cria o "estúdio fotográfico": um cubo de 6m com teto e duas paredes
    removidas, formando um fundo infinito (curva contínua chão-parede).

    Passos (seguindo exatamente a especificação):
        1. Cubo padrão (2m de aresta) escalado por 3 -> 6m de aresta.
        2. Deslocado +3m no eixo Z para que a base fique em Z=0 (o cubo,
           antes de mover, se estende de -3 a +3 em cada eixo).
        3. Remoção das faces Superior, Y-Negativo e X-Positivo, abrindo o
           estúdio para a câmera "entrar" visualmente.
        4. Inversão das normais restantes, para que a face voltada para
           DENTRO do estúdio (onde ficam a câmera e as letras) seja a
           face frontal renderizável.
    """
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))
    backdrop = bpy.context.active_object
    backdrop.name = "Backdrop"
    backdrop.scale = (3.0, 3.0, 3.0)
    backdrop.location.z = 3.0

    bpy.context.view_layer.objects.active = backdrop
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(backdrop.data)
    bm.faces.ensure_lookup_table()

    # Identifica as faces pela direção da normal (em espaço local, um
    # cubo recém-criado tem exatamente uma face por eixo/sentido).
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

    # Inverte as normais das faces restantes (chão + duas paredes), para
    # que a superfície "de dentro" do estúdio seja a que recebe luz e
    # aparece no render.
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()

    bpy.ops.object.mode_set(mode="OBJECT")

    print(f"[Backdrop] '{backdrop.name}' criado com {len(backdrop.data.polygons)} faces restantes.")
    return backdrop


def criar_material_das_letras():
    """Cria o material compartilhado 'letter material' (Principled BSDF).

    Assim como no Script 1 da Prática 7, não é preciso setar
    `use_nodes = True`: no Blender 5.2 todo Material já nasce com uma
    `node_tree` pronta.
    """
    material = bpy.data.materials.new(name="letter material")
    print(f"[Material] '{material.name}' criado.")
    return material


def criar_letra(nome, material):
    """Cria um objeto de texto 3D configurado conforme a especificação:
    rotacionado em pé, extrudado, centralizado e erguido do chão.
    """
    bpy.ops.object.text_add(location=(0, 0, 0.4))
    letra = bpy.context.active_object
    letra.name = nome

    dados_texto = letra.data
    dados_texto.body = nome
    dados_texto.align_x = "CENTER"
    dados_texto.align_y = "CENTER"
    dados_texto.extrude = 0.12

    # Em pé (rotação em torno de X) e origem elevada 0.4m para não colidir
    # com o chão do backdrop ao receber rotações 3D completas no Script 2.
    letra.rotation_euler = (math.radians(90), 0.0, 0.0)

    dados_texto.materials.append(material)

    print(f"[Letra] '{letra.name}' criada (extrude=0.12, origem em Z=0.4).")
    return letra


def criar_camera_e_luz():
    """Posiciona a câmera e a luz de acordo com os valores exatos da
    especificação.
    """
    bpy.ops.object.camera_add(
        location=(1.0, -1.0, 0.6),
        rotation=(math.radians(80), 0.0, math.radians(45)),
    )
    camera = bpy.context.active_object
    camera.name = "CameraDataset"
    bpy.context.scene.camera = camera

    # A especificação não define uma posição exata para o Point Light,
    # apenas o tipo. Posicionamos próxima à câmera e acima do sujeito,
    # um arranjo clássico de "estúdio" que evita sombras duras na letra.
    bpy.ops.object.light_add(type="POINT", location=(1.0, -1.0, 1.8))
    luz = bpy.context.active_object
    luz.name = "LuzDoEstudio"
    luz.data.energy = 200.0

    return camera, luz


def configurar_render_cycles():
    """Configura Cycles, GPU (quando disponível) e resolução 224x224.

    Nota de portabilidade: a especificação menciona "GPU Compute caso
    haja suporte a CUDA", pensando em GPUs NVIDIA. Aqui detectamos o
    backend de GPU correto para a plataforma atual (CUDA/OPTIX em
    Windows/Linux com NVIDIA, METAL no macOS) para que o script continue
    funcional em qualquer máquina.
    """
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
            continue  # backend não suportado nesta build/plataforma

        preferencias_cycles.get_devices()
        dispositivos_gpu = [
            dispositivo for dispositivo in preferencias_cycles.devices if dispositivo.type != "CPU"
        ]
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
    criar_backdrop()

    material = criar_material_das_letras()
    for nome in ("A", "B", "C"):
        criar_letra(nome, material)

    criar_camera_e_luz()
    configurar_render_cycles()


if __name__ == "__main__":
    main()
