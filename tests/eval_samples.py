#!/usr/bin/env python3
"""
Avalia o modelo treinado nas imagens de `assets/samples/`.

Compara a classe prevista com a esperada (deduzida do nome do arquivo, ex.:
`ferrugem_milho_1.jpg` -> esperado `ferrugem_milho`). Serve de evidência rápida
de que o modelo acerta as classes — bom pra mostrar no vídeo/PR.

    .venv/bin/python tests/eval_samples.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2  # noqa: E402
from src import config  # noqa: E402
from src.classifier import Classificador  # noqa: E402

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "samples")


def esperado_do_nome(fname: str) -> str:
    return os.path.splitext(fname)[0].rsplit("_", 1)[0]


def main() -> int:
    clf = Classificador(config.MODEL_PATH, config.FALLBACK_MODEL, config.IMG_SIZE)
    if clf.usando_fallback:
        print("[ERRO] Modelo treinado nao encontrado — rode o treino antes.")
        return 2

    arquivos = sorted(f for f in os.listdir(SAMPLES)
                      if f.lower().endswith((".jpg", ".jpeg", ".png")))
    if not arquivos:
        print(f"[ERRO] Sem imagens em {SAMPLES}")
        return 2

    acertos = 0
    print(f"{'arquivo':32s} {'esperado':26s} {'predito':26s} conf   ok")
    print("-" * 96)
    for f in arquivos:
        frame = cv2.imread(os.path.join(SAMPLES, f))
        if frame is None:
            continue
        pred = clf.prever(frame)
        esp = esperado_do_nome(f)
        ok = pred.classe == esp
        acertos += int(ok)
        print(f"{f:32s} {esp:26s} {pred.classe:26s} {pred.confianca*100:4.0f}%  "
              f"{'OK' if ok else 'X'}")

    n = len(arquivos)
    print("-" * 96)
    print(f"Acuracia nas amostras: {acertos}/{n} = {100*acertos/n:.1f}%")
    return 0 if acertos == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
