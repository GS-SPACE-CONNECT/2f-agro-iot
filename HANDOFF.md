# 🌅 HANDOFF — Olho na Folha (bom dia, Jota!)

Trabalhei a noite no `2f-agro-iot`. **O módulo de IoT está praticamente pronto.**
Tudo já montado e testado em **`~/dev/2f-agro-iot`** (com o `.venv` já criado).

## ✅ O que ficou pronto (overnight)

- **Script completo** `olho_na_folha.py` — modular, FPS na tela, tratamento de
  exceções no stream, integração com a API + fila offline. (rubrica: 30 pts)
- **Modelo treinado** `models/2fagro-folha-cls-v1.pt` (YOLOv8-cls, 6 classes). <!-- METRICAS -->
- **Dataset, treino e Colab** (`train/`) — dá pra retreinar quando quiser.
- **README com diagrama**, spec, plano e o **roteiro do vídeo** (`docs/roteiro-video.md`). (rubrica: 20 pts)
- **Testes headless** passando + 12 imagens de amostra em `assets/samples/`.
- **Branch `feat/olho-na-folha` + Draft PR** aberto (link no fim).
- Ambiente consertado (bug do numpy/torch resolvido — ver "Decisões").

## ⚡ Sua lista da manhã (~30–45 min, solo)

```bash
cd ~/dev/2f-agro-iot
source .venv/bin/activate
```

**1. Ver a demo rodando (2 min)** — confere que abre, classifica e mostra FPS:
```bash
python olho_na_folha.py                  # webcam ao vivo (aponte uma folha)
# sem webcam à mão? testa com as amostras:
python olho_na_folha.py --source assets/samples/
```

**2. 🎬 Gravar o VÍDEO (50 pts — a maior nota, só você consegue).**
Roteiro cronometrado pronto em [`docs/roteiro-video.md`](docs/roteiro-video.md).
Mostre: a tela rodando, o **FPS**, uma folha doente, uma saudável, e variando luz/oclusão.

**3. (Opcional) Retreinar com mais capricho no Colab** — se quiser acurácia/épocas
a mais pro vídeo: abra `train/colab_treino.ipynb`, ligue GPU, rode tudo, baixe o
`.pt` e substitua em `models/`.

**4. Validar e mergear o PR** (link no fim) depois que o vídeo estiver gravado.

## 📂 Onde está cada coisa

| Quero… | Arquivo |
| --- | --- |
| Rodar a demo | `olho_na_folha.py` |
| Roteiro do vídeo | `docs/roteiro-video.md` |
| Mexer nas classes/threshold | `src/config.py` |
| Retreinar | `train/` (+ `colab_treino.ipynb`) |
| Testar sem webcam | `python olho_na_folha.py --source assets/samples/` |
| Testar a API | `python tools/mock_api.py 5000` |

## 🔧 Decisões que tomei (e como reverter)

1. **Classificação (YOLOv8-cls)**, não detecção — você aprovou. Ver spec.
2. **6 classes**: café→ferrugem-do-milho (PlantVillage **não tem café**). Mexer em
   `train/prepare_dataset.py` (`SOURCE_TO_KEY`) + `src/config.py` se quiser trocar.
3. **Bug de ambiente resolvido:** o torch 2.2.2 (Intel Mac) quebra com numpy 2.x.
   Fixei `numpy==1.26.4` + `opencv==4.10`. Por isso o `requirements.txt` tem esses pins.
4. **Modelo versionado** no repo pra rodar out-of-the-box.

## ⚠️ Confere isto

- **Não testei a webcam de verdade** (não tenho câmera aqui) — o pipeline foi validado
  headless com imagens. O código da webcam é o mesmo caminho; só rode o passo 1.
- **RM do Lucca (554608):** peguei do README do SmartGym. Confirma se está certo no
  README/PR antes de entregar.
- O `.venv/`, `data/` e `runs/` estão no `.gitignore` (não vão pro git, de propósito).

## 🔗 Links

- **Draft PR:** _(link colado no resumo final do chat)_
- Board / epic IoT #1: https://github.com/orgs/GS-SPACE-CONNECT/projects/1
