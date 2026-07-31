# Prática 8 — Criação do Primeiro Dataset Sintético (III)

Scripts em Python (API `bpy`) para o **Blender 5.2.0 LTS**, implementando 
um pipeline completo de geração de dataset sintético — letras 3D
(`A`, `B`, `C`) renderizadas contra um estúdio fotográfico infinito, com
rotação e cor aleatórias, distribuídas em splits `train`/`val`/`test`.

## Conteúdo

| Arquivo | Descrição |
| --- | --- |
| [`01_configuracao_da_cena.py`](01_configuracao_da_cena.py) | Etapa 1: monta o backdrop (cubo de 6m com teto e duas paredes removidas + normais invertidas), cria as três letras 3D com material compartilhado `"letter material"`, posiciona câmera/luz e configura o render (Cycles, GPU quando disponível, 224x224, 128 samples). |
| [`01b_visualizar_render_estudio.py`](01b_visualizar_render_estudio.py) | Reaproveita o Script 1 e renderiza a letra `A` isolada, para conferência visual headless do enquadramento e do backdrop. |
| [`02_geracao_dataset_sintetico.py`](02_geracao_dataset_sintetico.py) | Etapa 2: `randomly_rotate_object` (rotação 3D 0–2π) e `randomly_change_color` (HSV, matiz aleatório com saturação/valor em 1.0), loop de geração com `hide_render` para isolar a letra ativa, nomenclatura `NNNNNN.png` via `zfill(6)` e cálculo de tempo restante estimado (ETA). |
| `dataset_amostra/` | Amostra do dataset gerado em **modo de teste** (`train`: 3, `val`: 2, `test`: 1 por letra — 18 imagens), commitada como prova de funcionamento do pipeline. |
| `renders/` | Render de conferência do Script 1b. |


## Como executar

Via terminal (headless):

```bash
cd "8 - Pratica: Criação do Primeiro Dataset Sintético (III)"
blender --background --python "01_configuracao_da_cena.py"
blender --background --python "02_geracao_dataset_sintetico.py"
```

Via interface gráfica: abra o Blender, vá ao workspace **Scripting**, abra
o arquivo desejado e rode com `Alt+P`.

### Gerando o dataset de produção completo

Por padrão, `02_geracao_dataset_sintetico.py` roda em **modo de teste**
(`MODO_TESTE = True`, 6 imagens por letra), salvando em
`dataset_amostra/` dentro do próprio projeto. Para gerar o dataset de
produção (300/80/10 imagens por letra — 1170 no total), edite a constante
no topo do arquivo:

```python
MODO_TESTE = False
```

Nesse modo a saída vai para `/tmp/abc_dataset` (fora do repositório) — de
propósito, para não versionar mais de mil imagens no git. Com Cycles em
GPU, a produção completa leva poucos minutos (ver nota de performance
abaixo).

## Notas técnicas

- **`__file__` vazio ao rodar pelo Text Editor**: `01b_visualizar_render_estudio.py`
  e `02_geracao_dataset_sintetico.py` localizam o Script 1 na mesma pasta
  via `__file__`. Isso funciona direto no modo headless, mas ao rodar via
  Alt+P no Text Editor do Blender — mesmo tendo aberto o arquivo do disco
  (não colado) — `__file__` frequentemente vem como string vazia (quirk
  do Blender), e não `NameError`. Combinado com o Blender iniciado pelo
  Finder/Dock usando `/` como diretório de trabalho, isso resultava em
  tentar abrir `/01_configuracao_da_cena.py`. A função
  `obter_diretorio_do_script()` cobre esse caso consultando
  `bpy.data.texts[...].filepath` (o caminho real do arquivo aberto) antes
  de cair para `os.getcwd()`.
- **CUDA vs. Metal**: a especificação original pede GPU Compute "caso haja
  suporte a CUDA" (cenário típico com GPU NVIDIA). Nesta máquina (Mac com
  GPU Apple Silicon) o backend correto do Cycles é **METAL**, não CUDA —
  `configurar_render_cycles()` testa os backends candidatos
  (`OPTIX`, `CUDA`, `HIP`, `METAL`, `ONEAPI`) em tempo de execução e usa o
  primeiro suportado pela plataforma, mantendo o script portável.
- **Custo de compilação de shaders na GPU**: a primeira renderização de
  uma sessão do Blender com Cycles em GPU paga um custo fixo de
  compilação de kernels (~100s nesta máquina). Da segunda renderização em
  diante, dentro do mesmo processo, cada imagem 224×224/128 samples leva
  ~0.5s. Por isso o Script 2 monta a cena e renderiza tudo em uma única
  execução do Blender — reabrir o processo a cada imagem pagaria esse
  custo de compilação repetidamente.
- **`use_nodes` obsoleto**: assim como nas Práticas 5 e 7, o material
  `"letter material"` não seta `use_nodes = True` — no Blender 5.2 todo
  `Material` já nasce com `node_tree` pronta.
- **Posição do Point Light**: a especificação não define coordenadas
  exatas para a luz, apenas o tipo (`Point Light`). Escolhemos posicioná-
  la próxima à câmera e acima do sujeito (arranjo clássico de estúdio),
  documentado em `criar_camera_e_luz()`.
- **Identificação das faces do backdrop por normal**: como o cubo é
  recém-criado (sem nenhuma transformação de malha ainda aplicada), cada
  face tem uma normal alinhada a exatamente um eixo, o que permite
  identificar programaticamente "face de cima", "face -Y" e "face +X" só
  comparando `face.normal` com cada eixo — sem precisar de índices fixos
  de face que quebrariam se a topologia do cubo mudasse.

## Próximos passos

Ainda não implementado: variação de iluminação (posição/intensidade
aleatórias da luz) e de fundo (cor do backdrop), além de um arquivo
`labels.json`/`metadata.csv` por split registrando o ângulo de rotação e
a cor exatos usados em cada imagem — útil para depuração e para tarefas de
regressão (não apenas classificação).
