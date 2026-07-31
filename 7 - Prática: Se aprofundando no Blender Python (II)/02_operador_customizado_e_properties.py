"""
Script 2 - Operador Customizado e Properties (estrutura de Add-on)
Blender 5.2.0 LTS | API Python (bpy)

Objetivo didático:
    Dar o próximo passo de profundidade em relação aos scripts "soltos"
    das práticas anteriores: em vez de só executar comandos em sequência,
    empacotamos a lógica em um `bpy.types.Operator` de verdade — a mesma
    classe usada para escrever add-ons —, com Properties customizadas que
    aparecem automaticamente no painel "Adjust Last Operation" (F9) do
    Blender. Corresponde aos capítulos "Python Templates", "Creating the
    Operator" e "Creating Properties" do vídeo "Python Crash Course for
    Blender" (Curtis Holt).

Estrutura de add-on (mesmo fora de um add-on de fato):
    O Blender > Text Editor > Templates > Python > "Operator Simple" gera
    exatamente este esqueleto: uma classe Operator + funções
    register()/unregister(). Seguir esse template mesmo em um script
    avulso é o que permite que o operador apareça no buscador de comandos
    (F3) e tenha suporte nativo a Undo (Ctrl+Z) depois de rodar.

Como executar:
    GUI:
        Abra este arquivo no workspace "Scripting" e rode com Alt+P.
        Depois, pressione F3 e busque por "Espalhar Cópias Aleatórias"
        para rodar o operador de novo com outros parâmetros.
    Headless (terminal):
        blender --background --python "02_operador_customizado_e_properties.py"
"""

import random

import bpy


def limpar_cena():
    """Remove com segurança todas as malhas, câmeras e luzes da cena atual."""
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


def criar_objeto_semente():
    """Cria o objeto original que será copiado pelo operador."""
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.4, location=(0, 0, 0))
    semente = bpy.context.active_object
    semente.name = "ObjetoSemente"
    return semente


class OBJECT_OT_espalhar_copias_aleatorias(bpy.types.Operator):
    """Duplica o objeto ativo em posições aleatórias ao redor da origem.

    Toda a configuração exposta aqui (Properties) vira automaticamente
    os campos do painel "Adjust Last Operation" (F9) depois de rodar o
    operador — não é preciso escrever nenhuma UI manualmente para isso.
    """

    bl_idname = "object.espalhar_copias_aleatorias"
    bl_label = "Espalhar Cópias Aleatórias"
    # REGISTER expõe o operador ao histórico/painel F9;
    # UNDO integra a ação ao Ctrl+Z nativo do Blender.
    bl_options = {"REGISTER", "UNDO"}

    quantidade: bpy.props.IntProperty(
        name="Quantidade",
        description="Número de cópias a espalhar",
        default=8,
        min=1,
        max=200,
    )
    raio: bpy.props.FloatProperty(
        name="Raio",
        description="Distância máxima em relação à origem",
        default=3.0,
        min=0.0,
    )
    semente_aleatoria: bpy.props.IntProperty(
        name="Semente Aleatória",
        description="Semente do gerador de números aleatórios, para resultados reprodutíveis",
        default=0,
    )

    @classmethod
    def poll(cls, context):
        """Controla quando o operador aparece habilitado (não acinzentado).

        Aqui exigimos um objeto do tipo malha ativo — sem isso, não faz
        sentido tentar duplicá-lo.
        """
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        """Corpo do operador: equivalente ao `main()` dos scripts avulsos,
        mas reexecutável a qualquer momento via F3 ou pelo painel F9 com
        parâmetros diferentes.
        """
        objeto_original = context.active_object
        gerador = random.Random(self.semente_aleatoria)

        for indice in range(self.quantidade):
            copia = objeto_original.copy()
            copia.data = objeto_original.data.copy()
            copia.name = f"{objeto_original.name}_copia_{indice:02d}"
            copia.location = (
                gerador.uniform(-self.raio, self.raio),
                gerador.uniform(-self.raio, self.raio),
                gerador.uniform(-self.raio, self.raio),
            )
            context.collection.objects.link(copia)

        self.report(
            {"INFO"},
            f"{self.quantidade} cópias espalhadas (raio={self.raio}, semente={self.semente_aleatoria}).",
        )
        return {"FINISHED"}


# Tupla de classes a (des)registrar. Mesmo com uma única classe, manter
# essa lista é o padrão usado em add-ons reais, o que facilita adicionar
# novos Operators/Panels/PropertyGroups no futuro sem mudar a estrutura.
CLASSES = (OBJECT_OT_espalhar_copias_aleatorias,)


def register():
    for classe in CLASSES:
        bpy.utils.register_class(classe)


def unregister():
    for classe in reversed(CLASSES):
        bpy.utils.unregister_class(classe)


def main():
    limpar_cena()
    semente = criar_objeto_semente()

    register()

    bpy.context.view_layer.objects.active = semente
    semente.select_set(True)

    # Chamamos o operador via `bpy.ops`, exatamente como o Blender faz
    # internamente quando um botão de painel é clicado — é a prova de que
    # a classe está corretamente registrada e utilizável como qualquer
    # operador nativo.
    bpy.ops.object.espalhar_copias_aleatorias(quantidade=12, raio=3.5, semente_aleatoria=42)

    print(f"[Operador] Objetos na cena após execução: {len(bpy.data.objects)}")

    # Propositalmente NÃO chamamos unregister() aqui: em uso real (dentro
    # do Blender, via Alt+P ou como add-on), o operador deve continuar
    # disponível no buscador F3 depois do script terminar. A função
    # unregister() existe para ser usada por um gerenciador de add-ons ou
    # ao recarregar o script manualmente.


if __name__ == "__main__":
    main()
