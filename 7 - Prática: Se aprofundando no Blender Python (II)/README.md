# Prática 7 — Se aprofundando no Blender Python (II)

Scripts em Python (API `bpy`) para o **Blender 5.2.0 LTS**, aprofundando a
manipulação de cena vista na Prática 5 com os tópicos centrais do vídeo
[Python Crash Course for Blender!](https://www.youtube.com/watch?v=XqX5wh4YeRw)
(Curtis Holt): modificadores, shading, materiais via nodes, e a estrutura
de Operator/Properties usada para escrever add-ons de verdade.

## Conteúdo

| Arquivo | Descrição |
| --- | --- |
| [`01_modificadores_e_materiais.py`](01_modificadores_e_materiais.py) | Pilha de modificadores não-destrutivos (`Bevel` + `Subdivision Surface`), sombreamento suave por ângulo (`shade_smooth_by_angle`) e um material com árvore de nodes (`Principled BSDF` + `Noise Texture` procedural conectada à Roughness). |
| [`01b_visualizar_render_material.py`](01b_visualizar_render_material.py) | Reaproveita o Script 1, adiciona câmera e luz, e renderiza a cena em PNG para conferência visual headless. |
| [`02_operador_customizado_e_properties.py`](02_operador_customizado_e_properties.py) | Empacota lógica em um `bpy.types.Operator` de verdade (`OBJECT_OT_espalhar_copias_aleatorias`), com `Properties` (`IntProperty`/`FloatProperty`) que espalham cópias aleatórias de um objeto. Segue o template padrão de add-on (`register`/`unregister` + `bl_idname`/`bl_label`/`bl_options`). |
| [`02b_visualizar_render_operador.py`](02b_visualizar_render_operador.py) | Reaproveita o Script 2 e renderiza o resultado do espalhamento de cópias para conferência visual headless. |
| `renders/` | Imagens de exemplo geradas pelos scripts acima. |

## Como executar

Via terminal (headless):

```bash
cd "7 - Prática: Se aprofundando no Blender Python (II)"
blender --background --python "01_modificadores_e_materiais.py"
blender --background --python "02_operador_customizado_e_properties.py"
```

Via interface gráfica: abra o Blender, vá ao workspace **Scripting**, abra
o arquivo desejado e rode com `Alt+P`. Depois de rodar o Script 2, pressione
`F3` e busque por "Espalhar Cópias Aleatórias" para executar o operador de
novo com outros parâmetros, ou abra o painel "Adjust Last Operation" (canto
inferior esquerdo da viewport) logo após rodá-lo para ajustar as
`Properties` sem reescrever nada.

## Notas técnicas

- **`use_nodes` está obsoleto**: a partir do Blender 5.2, todo `Material`
  já nasce com uma `node_tree` pronta — a propriedade `use_nodes` está
  marcada para remoção no Blender 6.0 (`DeprecationWarning`). O Script 1
  acessa `material.node_tree` diretamente, sem setar `use_nodes = True`.
- **Shade Smooth "burro" vs. por ângulo**: `bpy.ops.object.shade_smooth()`
  simples suaviza todas as faces, arredondando quinas que deveriam
  continuar duras. Desde o Blender 4.1, `shade_smooth_by_angle(angle=...)`
  é a forma recomendada: só suaviza onde o ângulo entre normais fica
  abaixo do limiar informado, preservando quinas mais fechadas.
- **Ordem de modificadores importa**: o `Bevel` foi posicionado ANTES do
  `Subdivision Surface` na pilha propositalmente — ele arredonda as
  arestas do cubo original antes de a malha ser subdividida. Trocar a
  ordem faria o Bevel operar sobre uma topologia já suavizada, com
  resultado bem menos previsível.
- **Operator como estrutura de add-on**: mesmo fora de um add-on
  instalado, seguir o template `bpy.types.Operator` + `register()`/
  `unregister()` (o mesmo gerado por Text Editor → Templates → Python →
  "Operator Simple") dá de graça undo nativo (`bl_options = {"REGISTER",
  "UNDO"}`), aparição no buscador de comandos (F3) e os campos do painel
  F9 gerados automaticamente a partir das `Properties` da classe — sem
  escrever nenhuma UI manualmente.

## Próximos passos

Ainda não implementado: um `Panel` (`bpy.types.Panel`) na barra lateral
(N-panel) da viewport para expor as `Properties` do operador antes de
rodá-lo (hoje elas só ficam visíveis depois, no painel F9), e persistência
de parâmetros customizados via `PropertyGroup` anexado à `Scene`.
