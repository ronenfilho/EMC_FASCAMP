# Prática 10 — Anotação Automática dentro do Blender (III)

Scripts em Python (API `bpy`) para o **Blender 5.2.0 LTS**: pipeline de
geração automática de máscaras de segmentação semântica a partir do
`pass_index` de objetos, usando o Compositor de nós — duas abordagens
complementares (rampa de cinza normalizada e máscaras binárias por
objeto via `ID Mask`).

## Conteúdo

| Arquivo | Descrição |
| --- | --- |
| [`01_configuracao_da_cena.py`](01_configuracao_da_cena.py) | `setup_render_properties()` (Cycles + GPU quando disponível), `create_test_scene()` (Cubo/Esfera/Cone com `pass_index` 1/27/200), `habilitar_pass_object_index()` (expõe `Object Index` no compositor). |
| [`01b_visualizar_render_cena.py`](01b_visualizar_render_cena.py) | Reaproveita o Script 1 e renderiza a cena normal (colorida, sem compositor), para conferência visual do enquadramento. |
| [`02_mascara_grayscale.py`](02_mascara_grayscale.py) | Abordagem A: `configure_compositor_grayscale(bit_depth)` — Render Layers → Math (Divide por 255 ou 65535) → saída do compositor, exportando uma máscara em tons de cinza em 8-bit e outra em 16-bit. |
| [`03_mascaras_binarias_idmask.py`](03_mascaras_binarias_idmask.py) | Abordagem B: `configure_compositor_binary_masks()` — um nó `ID Mask` por objeto, exportando uma máscara estritamente binária (preto/branco, sem anti-aliasing) para cada um. |
| `renders/` | Amostras de saída: render normal, as duas máscaras grayscale e as três máscaras binárias. |

## Como executar

Via terminal (headless):

```bash
cd "10 - Prática: Anotação Automática dentro do Blender (III)"
blender --background --python "01_configuracao_da_cena.py"
blender --background --python "02_mascara_grayscale.py"
blender --background --python "03_mascaras_binarias_idmask.py"
```

Via interface gráfica: workspace **Scripting** → **Open** (não colar o
texto, ver nota sobre `__file__` no README da Prática 8) → `Alt+P`.
Depois de qualquer um dos Scripts 2/3, `F12` renderiza usando a última
árvore de compositor montada.

## Notas técnicas (API do Compositor mudou bastante desde a especificação original)

A especificação de origem foi escrita pensando no Blender 2.83. Entre a
2.83 e a 5.2 o Compositor foi reescrito internamente (a árvore de nós
virou um node group de verdade, como os de Geometry Nodes). Nada do
código original rodava sem adaptação; o mapeamento ficou assim:

- **`scene.node_tree` não existe mais**: a árvore do compositor agora é
  um data-block próprio (`bpy.data.node_groups`, tipo
  `CompositorNodeTree`) atribuído via `scene.compositing_node_group`.
  `scene.use_nodes = True` sozinho não cria mais essa árvore.
- **`IndexOB` agora se chama `Object Index`**: mesmo dado, saída do nó
  Render Layers renomeada. Ela só aparece na lista de `outputs` do nó
  se o motor de render **já estiver em Cycles** *antes* de o nó ser
  criado — mudar o engine depois não atualiza os sockets já existentes.
- **`CompositorNodeMath` não existe mais**: o nó de matemática genérico
  agora é `ShaderNodeMath`, compartilhado entre os editores de Shading e
  Compositing.
- **`CompositorNodeComposite` foi removido**: como a árvore virou um
  node group, a saída final agora é um `NodeGroupOutput` normal, ligado
  a um socket declarado em `tree.interface.new_socket(...)`.
- **`ID Mask` perdeu suas propriedades fixas**: `Index` e `Anti-Alias`
  eram propriedades do nó no Blender 2.83; nesta versão são **entradas**
  (`node.inputs['Index'].default_value`, `node.inputs['Anti-Alias'].default_value`).
- **O nó `File Output` também mudou de API** (`file_slots` virou
  `file_output_items`, com `item.override_node_format` para formato por
  slot), mas nos testes desta prática ele se mostrou pouco confiável
  para exportar um único canal como PNG "cru" (o resultado sempre saía
  como um `Unsaved.exr` genérico, ignorando o formato/nome configurado
  no item — possível limitação/bug desta versão). A solução adotada foi
  renderizar cada máscara como a **saída principal** da cena
  (`scene.render.filepath` + `write_still=True`), trocando a ligação do
  Group Output entre uma renderização e outra — mesmo resultado prático,
  API mais estável.
- **O bug mais sério: AgX distorce até dados "não-cor"**. Por padrão, o
  Blender 5.2 aplica o *view transform* **AgX** a qualquer imagem salva
  — mesmo a um canal matematicamente normalizado para representar um
  índice inteiro, não uma cor de verdade. Medido nesta prática: o
  `pass_index` 27 (dividido por 255 = 0.1059) devia virar o pixel `27`,
  mas com AgX ativo virava `92`; o índice `200` virava `229` em vez de
  `200`. Esse é exatamente o problema que o relatório de origem descreve
  ("o gerenciamento de cores distorce valores RGB puros"), só que também
  afeta a técnica de normalização por divisão — não só cores sólidas.
  A correção: `image_settings.color_management = 'OVERRIDE'` +
  `image_settings.view_settings.view_transform = 'Raw'` antes de
  renderizar. Validado byte a byte após a correção: `pass_index`
  1/27/200 → pixel 1/27/200 exatos, nos dois formatos (8-bit e 16-bit).
- **Verificação de imagens 16-bit via `bpy.data.images.load()`**: ao
  conferir o resultado programaticamente, é preciso setar
  `imagem.colorspace_settings.name = 'Non-Color'` antes de ler
  `.pixels` — do contrário o Blender decodifica os valores como se
  fossem sRGB codificado, distorcendo a leitura (não o arquivo salvo,
  que está correto).

## Próximos passos

Ainda não implementado: a extensão para geometria projetiva e bounding
boxes (matriz de projeção `P = K[R|t]`) para exportar coordenadas 2D de
objetos, incluindo o tratamento de oclusão via *raycasting* mencionado
como dificuldade na pesquisa que inspirou esta prática — aplicável a um
cenário mais complexo (múltiplos objetos do mesmo tipo, câmera móvel).
