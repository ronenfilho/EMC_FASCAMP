# Prática 9 — Datasets Sintéticos com Objetos Reais (III)

Scripts em Python (API `bpy`) para o **Blender 5.2.0 LTS**: geração de um
dataset sintético fotorrealista de uma caneca de vidro com chá em
diferentes níveis, usando materiais de vidro/líquido volumétrico e um rig
de câmera baseado em curvas NURBS para cobrir múltiplos ângulos sem nunca
mostrar o "vazio" fora do cenário.

## Conteúdo

| Arquivo | Descrição |
| --- | --- |
| [`01_configuracao_da_cena.py`](01_configuracao_da_cena.py) | Importa `tea_mug.fbx`, configura os materiais `Glass` (Transmission=1.0/Roughness=0.0) e `Tea` (idem + node `Volume Absorption`), monta o backdrop de canto, a iluminação (Area 1x1m/21W + Sun 0.03) e o rig de câmera NURBS completo (arco de elevação + elipse de azimute + `Track To`). |
| [`01b_visualizar_render_estudio.py`](01b_visualizar_render_estudio.py) | Reaproveita o Script 1 e renderiza a caneca cheia na posição neutra do rig, para conferência visual headless. |
| [`02_geracao_dataset_sintetico.py`](02_geracao_dataset_sintetico.py) | Etapa 2: `randomizar_rig_de_camera`, `randomizar_rotacao_caneca` e `randomizar_cor_do_cha` (Domain Randomization), loop de geração para as 4 classes de nível de líquido, splits `train`/`val`/`test`, nomenclatura `zfill(6)` e ETA em tempo real (mesmo padrão da Prática 8). |
| `dataset_amostra/` | Amostra do dataset gerado em **modo de teste** (6 imagens por classe × 4 classes = 24), commitada como prova de funcionamento. |
| `renders/` | Render de conferência do Script 1b. |
| [`tea_mug.fbx`](tea_mug.fbx) | Modelo 3D da caneca (malhas `Glass_Mug`, `Full`, `Half-Full`, `Mostly-Empty`). |

## Como executar

Via terminal (headless):

```bash
cd "9 - Prática: Datasets Sintéticos com Objetos Reais (III)"
blender --background --python "01_configuracao_da_cena.py"
blender --background --python "02_geracao_dataset_sintetico.py"
```

Via interface gráfica: workspace **Scripting** → **Open** (não colar o
texto — ver nota técnica sobre `__file__` abaixo) → `Alt+P`.

### Gerando o dataset de produção completo

Por padrão, `02_geracao_dataset_sintetico.py` roda em **modo de teste**
(`MODO_TESTE = True`). Para o dataset completo (300/80/10 imagens por
classe × 4 classes = 1560 imagens), troque:

```python
MODO_TESTE = False
```

A saída vai para `/tmp/tea_dataset` (fora do repositório), pelo mesmo
motivo da Prática 8: não versionar milhares de imagens no git.

## Decisões de design (onde a especificação era ambígua ou inconsistente)

- **4 classes, não 3**: o roteiro define `CLASSES = ["empty", "half_full",
  "full"]`, mas o `tea_mug.fbx` traz 4 malhas de líquido em potencial
  (`Full`, `Half-Full`, `Mostly-Empty`, e a caneca vazia sem nenhuma
  visível) e o `relatorio-datasets-sinteticos.md` também descreve 4
  estados ("cheio, meio cheio, quase vazio e vazio"). Optamos por usar as
  4 classes reais do asset: `empty`, `mostly_empty`, `half_full`, `full`.
- **Amostras/samples do Cycles**: o roteiro (script executável) usa
  `scene.cycles.samples = 128`, mas o relatório menciona 256 nas
  "Dificuldades". Ficamos com 128 (o valor que está no código-fonte
  reproduzível, não em prosa) — mesmo valor usado nas Práticas 7 e 8.
- **Posição da luz e ponto de foco exatos**: a especificação descreve as
  posições qualitativamente ("na frente e acima do copo", "centro
  volumétrico da caneca"). A Area Light foi posicionada em
  `(0.18, -0.22, 0.32)` olhando para o canto, e `object_target` é
  calculado programaticamente a partir do *bounding box* de `Glass_Mug`
  (em vez de um valor fixo), para continuar correto mesmo se o modelo
  importado mudar.
- **Tamanho do backdrop**: a especificação sugere escalar o cubo para
  `0.3`. Nos testes visuais isso deixava uma pequena fresta do "vazio"
  num canto do quadro mesmo na posição neutra do rig (offset=0 nas duas
  curvas). Aumentamos para `0.45` — resolve sem exigir mudanças no rig.

## Notas técnicas (descobertas depurando o rig de câmera)

Esta foi de longe a parte mais delicada da prática. Três bugs distintos
apareceram, cada um causando sintomas confusos (câmera "dentro" do
objeto, distância pulando de ~0 a 2× o raio esperado, quadros
inteiramente pretos):

1. **`Follow Path` só avança com offset NEGATIVO**: com `path_duration =
   100`, `offset = 0` é o início da curva, mas `offset` POSITIVO faz o
   Blender extrapolar para TRÁS do início (já visto nas Práticas 5 e 7,
   esquecido aqui e redescoberto do zero). A randomização em
   `randomizar_rig_de_camera` usa `random.uniform(0.0, -100.0)` — nunca
   um intervalo positivo.
2. **`Follow Path` SOMA a `.location` própria do objeto por cima do ponto
   calculado na curva** (diferente de `Child Of`, que cancela via
   `inverse_matrix`). Os Empties do rig (`circle_path_container`,
   `camera_container`) precisam ser criados em `(0, 0, 0)` — quem define
   a posição real é só a constraint.
3. **Escala não uniforme + rotação herdada via `Child Of` causa
   cisalhamento (*shear*)**: a primeira versão da elipse usava
   `bpy.ops.curve.primitive_nurbs_circle_add()` + `object.scale.y` para
   achatar. Combinado com a rotação que o `circle_path_container` herda
   do arco, isso distorcia a órbita da câmera (distâncias saltando de
   ~0.05 a ~0.7 em vez de variar suavemente). A correção foi construir a
   elipse já com os pontos de controle no formato elíptico (raios `x` e
   `y` diferentes desde a criação), mantendo a escala do objeto em
   `(1, 1, 1)`.
4. **Raio da elipse**: mesmo corrigido o cisalhamento, um raio de elipse
   igual ao do arco (0.35) levava os pontos nas "pontas" do eixo maior
   (diametralmente opostos) longe demais ou para o lado errado do alvo,
   chegando a renderizar um quadro **inteiramente preto** em um caso
   testado. Reduzir o raio da elipse para `0.15` (bem menor que o raio do
   arco) resolveu — validado em 26 combinações de teste (6 casos extremos
   + 20 aleatórios), todas sem vazamento de vazio.
5. **`arco.matrix_world` lido antes de o Blender atualizar a
   transformação**: depois de setar `objeto_curva.location` e
   `.rotation_euler`, ler `matrix_world` imediatamente ainda retorna a
   matriz "crua" (identidade) — é preciso `bpy.context.view_layer.update()`
   antes. Sem isso, `ponto_horizonte` saía como `(0.35, 0, 0)` em vez do
   ponto real já deslocado/rotacionado para a diagonal do backdrop.
6. **`__file__` dentro do Blender não é o caminho do arquivo** (lição da
   Prática 8, reaplicada aqui desde o início): `obter_diretorio_do_script()`
   consulta `bpy.data.texts[...].filepath` antes de `__file__`.

## Próximos passos

Ainda não implementado: Etapa 2 do roteiro (classificador TensorFlow/
MobileNetV2 via `ImageDataGenerator`, treinado sobre este dataset). Não
incluído nesta rodada porque TensorFlow/TensorFlow-Hub/Jupyter não estão
instalados neste ambiente — decisão tomada para manter o escopo desta
prática focado na parte Blender, como na Prática 8.
