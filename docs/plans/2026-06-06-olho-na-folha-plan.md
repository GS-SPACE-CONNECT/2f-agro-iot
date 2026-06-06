# Plano de Execução · Olho na Folha (2f-agro-iot)

**Prazo GS:** zip final no Teams em **09/06**. Este módulo (100 pts) precisa estar
fechado até 08/06 com folga.

## Mapa das issues do board (epic IoT #1)

| Issue | Tarefa | Status |
| --- | --- | --- |
| #2 | Setup ambiente Python + YOLOv8 | ✅ venv + `requirements.txt` fixo |
| #3 | Dataset PlantVillage (6 classes, split) | ✅ `prepare_dataset.py` |
| #4 | Fine-tuning YOLOv8(-cls) | ✅ `train.py` + Colab |
| #5 | Script principal `olho_na_folha.py` | ✅ modular + exceções + FPS |
| #6 | Integração API `POST /diagnostico` | ✅ `api_client.py` + fila offline |
| #7 | Vídeo demo (50 pts) | ⏳ roteiro pronto — **gravar (humano)** |
| #8 | README + requirements + diagrama | ✅ |

## Sequência executada (overnight)

1. **Setup** — venv isolado, deps instaladas, dataset baixado (mirror público).
2. **Dados** — 6 classes, 600 img/classe, split 80/20 (2880 train / 720 val).
3. **Código** — módulos `src/` + entrypoint; smoke test headless verde.
4. **Correção de ambiente** — pin `numpy<2` + `opencv==4.10` (torch 2.2.2 / Intel Mac).
5. **Treino** — YOLOv8n-cls local (CPU, 20 épocas) → `models/2fagro-folha-cls-v1.pt`.
6. **Validação e2e** — demo headless nas amostras + mock da API.
7. **Entrega** — branch `feat/olho-na-folha` + draft PR + `HANDOFF.md`.

## O que fica pro humano (ver HANDOFF.md)

- **Gravar o vídeo** (50 pts) — único item que precisa de webcam + pessoa.
- Conferir a demo ao vivo na própria máquina.
- (Opcional) retreinar no Colab pra mais épocas/imagens, se quiser.
- Validar e mergear o PR.

## Decisões travadas (reversíveis)

- **Classificação** (YOLOv8-cls), não detecção — ver spec.
- **6 classes** com café→ferrugem-do-milho (PlantVillage não tem café).
- Modelo **versionado** no repo pra rodar out-of-the-box.
