"""
Script 1 - Configuração da Cena de Teste para Segmentação (Pass Index)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Montar a cena mínima necessária para demonstrar o pipeline de
    anotação automática por máscaras de segmentação: três objetos
    distintos (Cubo, Esfera UV, Cone), cada um com um `pass_index`
    exclusivo, câmera e luz apontadas para o grupo, motor Cycles com GPU
    quando disponível, e a passagem de índice de objeto (`IndexOB`)
    habilitada na View Layer — pré-requisito para os Scripts 2 e 3
    lerem esse canal no compositor.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" (via "Open", não
        colando o texto) e rode com Alt+P.
    Headless (terminal):
        blender --background --python "01_configuracao_da_cena.py"
"""

import os

import bpy


def obter_diretorio_do_script(nome_do_arquivo):
    """Descobre a pasta onde este script está salvo em disco.

    Dentro do Blender, `__file__` NÃO é o caminho do arquivo — é sempre
    `"/" + nome_do_texto`, mesmo com o arquivo aberto do disco via Alt+P
    (lição das Práticas 8 e 9). Por isso `bpy.data.texts[...].filepath`
    é consultado primeiro; `__file__` só é confiável no modo headless.
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

# pass_index de cada objeto: 0 é reservado para o fundo por convenção do
# Blender, por isso todos os objetos de interesse usam valores >= 1.
OBJETOS_E_INDICES = {
    "Cubo": 1,
    "Esfera": 27,
    "Cone": 200,
}


def relatar_modo_de_execucao():
    """Registra se o Blender está rodando headless (--background) ou com
    interface gráfica — útil para diagnosticar comportamento diferente
    entre os dois modos (ex.: `bpy.ops.render.render` não abre uma janela
    de imagem em modo headless).
    """
    modo = "headless (--background)" if bpy.app.background else "interface gráfica (GUI)"
    print(f"[Ambiente] Blender rodando em modo: {modo}")
    return bpy.app.background


def limpar_cena():
    """Remove com segurança todos os objetos e purga data-blocks órfãos."""
    for objeto in list(bpy.data.objects):
        bpy.data.objects.remove(objeto, do_unlink=True)

    for colecao in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
        for bloco in list(colecao):
            if bloco.users == 0:
                colecao.remove(bloco)


def setup_render_properties():
    """Configura o motor de renderização: troca de EEVEE para Cycles e
    habilita GPU quando disponível.

    Nota de portabilidade: a especificação pede o "dispositivo
    GPU_COMPUTE", termo genérico do vídeo de origem (pensado em GPUs
    NVIDIA/CUDA). Aqui detectamos o backend correto por plataforma
    (OPTIX/CUDA/HIP/METAL/ONEAPI), mesma lógica usada nas Práticas 8 e 9.
    """
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"

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

    print(f"[Render] Engine=Cycles | Dispositivo={dispositivo_usado}")
    return dispositivo_usado


def create_test_scene():
    """Cria o Cubo, a Esfera UV e o Cone dispostos lado a lado em frente
    à câmera, cada um com seu `pass_index` exclusivo em Object Properties
    → Relations (`objeto.pass_index`).
    """
    bpy.ops.mesh.primitive_cube_add(size=1.4, location=(-2.2, 0, 0))
    cubo = bpy.context.active_object
    cubo.name = "Cubo"

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(0, 0, 0))
    esfera = bpy.context.active_object
    esfera.name = "Esfera"
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_cone_add(radius1=0.9, depth=1.8, location=(2.2, 0, 0))
    cone = bpy.context.active_object
    cone.name = "Cone"

    objetos = {"Cubo": cubo, "Esfera": esfera, "Cone": cone}
    for nome, objeto in objetos.items():
        objeto.pass_index = OBJETOS_E_INDICES[nome]
        print(f"[Objeto] '{nome}' criado com pass_index={objeto.pass_index}.")

    bpy.ops.object.camera_add(location=(0, -8, 2.5), rotation=(1.3, 0.0, 0.0))
    camera = bpy.context.active_object
    camera.name = "CameraSegmentacao"
    bpy.context.scene.camera = camera

    bpy.ops.object.light_add(type="SUN", location=(2, -4, 6))
    sol = bpy.context.active_object
    sol.data.energy = 3.0

    return objetos, camera, sol


def habilitar_pass_object_index():
    """Ativa a passagem `IndexOB` na View Layer atual — sem isso, o nó
    Render Layers no compositor não expõe o socket com os `pass_index`
    dos objetos, e os Scripts 2/3 não têm o que ler.
    """
    view_layer = bpy.context.view_layer
    view_layer.use_pass_object_index = True
    print(f"[ViewLayer] '{view_layer.name}': use_pass_object_index = True (expõe a saída IndexOB).")


def configurar_resolucao(largura=480, altura=320):
    scene = bpy.context.scene
    scene.render.resolution_x = largura
    scene.render.resolution_y = altura
    scene.render.image_settings.file_format = "PNG"


def main():
    limpar_cena()
    relatar_modo_de_execucao()
    setup_render_properties()
    create_test_scene()
    habilitar_pass_object_index()
    configurar_resolucao()


if __name__ == "__main__":
    main()
