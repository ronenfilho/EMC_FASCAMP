# Prática 5 — O que é Blender? (II)

Scripts em Python (API `bpy`) para o **Blender 5.2.0 LTS**, cobrindo os
fundamentos de manipulação tridimensional e o rigging de câmera orbital
apresentados nas aulas práticas.

## Conteúdo

| Arquivo | Descrição |
| --- | --- |
| [`01_manipulacao_3d_e_modos_de_malha.py`](01_manipulacao_3d_e_modos_de_malha.py) | Fundamentos geométricos: limpeza segura da cena, criação de uma malha primitiva, transição entre Object Mode e Edit Mode, e manipulação de vértices/arestas/faces via `bmesh`. Inclui notas didáticas sobre Tris, Quads e N-gons. |
| [`01b_visualizar_execucao_render.py`](01b_visualizar_execucao_render.py) | Reaproveita o Script 1, adiciona câmera e luz, e renderiza a cena em PNG — útil para visualizar o resultado mesmo rodando em modo headless. |
| [`02_rigging_de_camera_com_constraints.py`](02_rigging_de_camera_com_constraints.py) | Rig de câmera orbital: Empty de foco (`track_to_empty`), trilho circular NURBS (`CameraPath`), container (`camera_container`) e a câmera com as constraints `Track To` + `Child Of` na ordem correta, animadas para dar uma volta completa (frames 1 a 100). |
| [`02b_visualizar_orbita_render.py`](02b_visualizar_orbita_render.py) | Reaproveita o Script 2 e renderiza frames da órbita para conferência visual headless. |
| `renders/` | Imagens de exemplo geradas pelos scripts acima. |

## Como executar

Via terminal (headless):

```bash
cd "5 - Prática: O que é Blender?(II)"
blender --background --python "01_manipulacao_3d_e_modos_de_malha.py"
blender --background --python "02_rigging_de_camera_com_constraints.py"
```

Via interface gráfica: abra o Blender, vá ao workspace **Scripting**, abra
o arquivo desejado e rode com `Alt+P`. Para ver a órbita da câmera
funcionando, pressione a barra de espaço na Timeline após rodar o Script 2.

## Notas técnicas

- **Reordenação de constraints**: `Child Of` precisa ser movida para o topo
  da pilha (antes de `Track To`) e sua `inverse_matrix` precisa ser zerada
  manualmente — do contrário a câmera herda um deslocamento fixo do
  tamanho do raio do trilho (ver comentários em `02_rigging_de_camera_com_constraints.py`).
- **Actions no Blender 5.2**: o sistema de Actions "layered" (introduzido
  no Blender 4.4) removeu o acesso direto via `action.fcurves`; os scripts
  usam `action.fcurve_ensure_for_datablock` para continuar compatíveis.
- **Trilho circular**: apesar do nome da constraint ser "Follow Path", a
  primitiva "NURBS Path" é uma curva aberta. Para uma órbita fechada de
  360°, os scripts usam uma **NURBS Circle** em seu lugar.

## Próximos passos

Ainda não implementado: um pipeline de geração de dados sintéticos
(Script 3), com randomização de domínio (luz, rotação do alvo, offset de
câmera) e exportação de metadados de pose em `annotations.json`, pensado
para rodar em modo headless em escala.
