#!/usr/bin/env python3
"""
Smoke test headless — valida os módulos sem precisar de webcam nem do backend.

Roda:
    .venv/bin/python tests/smoke_test.py

Cobre: config, overlay (desenho), api_client (fila offline), camera (pasta de
imagens) e — se o ultralytics estiver instalado — o classifier no modelo fallback.
Sai com código != 0 se algo falhar (serve de gate antes do PR).
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
import cv2  # noqa: E402

from src import config  # noqa: E402
from src.api_client import ApiClient  # noqa: E402
from src.camera import FonteDeFrames  # noqa: E402
from src.config import info_classe  # noqa: E402
from src.overlay import desenhar_hud  # noqa: E402

falhas = []


def checar(nome: str, cond: bool, detalhe: str = "") -> None:
    status = "PASS" if cond else "FALHA"
    print(f"  [{status}] {nome}" + (f" — {detalhe}" if detalhe and not cond else ""))
    if not cond:
        falhas.append(nome)


def test_config():
    print("config:")
    c = info_classe("ferrugem_milho")
    checar("classe conhecida", c.label == "Ferrugem (milho)" and not c.saudavel)
    checar("classe saudavel", info_classe("saudavel").saudavel)
    desconhecida = info_classe("classe_xyz")
    checar("classe desconhecida nao quebra", desconhecida.label == "classe_xyz")


def test_overlay():
    print("overlay:")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    out = desenhar_hud(frame, "Ferrugem (milho)", 0.91, 12.3, saudavel=False,
                       enviando=True)
    checar("HUD desenha e mantem shape", out.shape == (480, 640, 3))
    checar("HUD alterou pixels", bool(out.any()))


def test_api_offline():
    print("api_client (fila offline):")
    with tempfile.TemporaryDirectory() as d:
        fila = os.path.join(d, "q.jsonl")
        api = ApiClient("http://127.0.0.1:59999/api/diagnostico", fila,
                        min_interval_s=0.0, timeout=0.5)
        st = api.enviar("ferrugem_milho", 0.95)
        checar("API fora -> enfileira", st in ("enfileirado", "desligado"), st)
        checar("fila tem 1 item", api.tamanho_fila() == 1, str(api.tamanho_fila()))
        # throttle: segundo envio imediato da mesma praga é ignorado
        api2 = ApiClient("http://127.0.0.1:59999/api/diagnostico", fila,
                         min_interval_s=999, timeout=0.5)
        api2.enviar("praga_x", 0.9)
        checar("throttle ignora repetido", api2.enviar("praga_x", 0.9) == "throttled")


def test_camera_imagens():
    print("camera (pasta de imagens):")
    with tempfile.TemporaryDirectory() as d:
        for i in range(3):
            cv2.imwrite(os.path.join(d, f"img{i}.jpg"),
                        np.full((64, 64, 3), i * 40, dtype=np.uint8))
        fonte = FonteDeFrames(d, loop=True)
        ok, frame = fonte.ler()
        checar("le imagem da pasta", ok and frame is not None)
        fonte.liberar()


def test_classifier_opcional():
    print("classifier (opcional — precisa ultralytics + rede):")
    try:
        from src.classifier import Classificador
        clf = Classificador(config.MODEL_PATH, config.FALLBACK_MODEL, config.IMG_SIZE)
        frame = np.full((224, 224, 3), 120, dtype=np.uint8)
        pred = clf.prever(frame)
        checar("inferencia retorna classe+conf",
               isinstance(pred.classe, str) and 0.0 <= pred.confianca <= 1.0)
    except Exception as e:
        print(f"  [SKIP] classifier nao testado: {e}")


def main() -> int:
    print("=== SMOKE TEST · Olho na Folha ===")
    test_config()
    test_overlay()
    test_api_offline()
    test_camera_imagens()
    test_classifier_opcional()
    print("\nResultado:", "TUDO PASSOU ✅" if not falhas else f"FALHAS: {falhas}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    raise SystemExit(main())
