"""Valida a heurística de fogo nos 3 sinais (cor, área, cintilação).

Casos:
  POSITIVO  chama sintética com flicker  -> DEVE detectar
  NEGATIVO  folha verde real (samples)   -> NÃO pode detectar (cor errada)
  NEGATIVO  laranja chapado estático     -> NÃO pode detectar (sem cintilação)

Não precisa de webcam: geramos os frames. Bom como evidência reproduzível.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np

from src import config
from src.fogo import DetectorFogo

H, W = 480, 640
rng = np.random.default_rng(42)  # determinístico


def frame_chama(t: int) -> np.ndarray:
    """Chama sintética: blobs quentes na base, perturbados a cada frame (flicker)."""
    img = np.zeros((H, W, 3), np.uint8)
    cx = W // 2 + int(20 * np.sin(t / 3.0))
    base_y = int(H * 0.85)
    for _ in range(40):
        dx = int(rng.normal(0, 55))
        dy = int(abs(rng.normal(0, 90)))
        x = np.clip(cx + dx, 0, W - 1)
        y = np.clip(base_y - dy, 0, H - 1)
        raio = int(rng.integers(10, 34))
        altura = (base_y - y) / (H * 0.6)            # 0 na base -> 1 no topo
        # Base avermelhada -> topo amarelo/branco (BGR).
        r = 255
        g = int(np.clip(60 + altura * 200 + rng.integers(-20, 20), 0, 255))
        b = int(np.clip(altura * 120 + rng.integers(-10, 30), 0, 255))
        cv2.circle(img, (int(x), int(y)), raio, (b, g, r), -1)
    return cv2.GaussianBlur(img, (0, 0), 3)


def frame_laranja_estatico(_t: int) -> np.ndarray:
    """Pôr do sol: tela quente e brilhante, mas IDÊNTICA frame a frame."""
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (30, 130, 245)  # BGR ~ laranja brilhante
    return img


def rodar(nome: str, gen, n=40, ultimos=15):
    det = DetectorFogo(conf_threshold=config.FOGO_CONF_THRESHOLD)
    estados, detec, confs = [], [], []
    for t in range(n):
        r = det.analisar(gen(t))
        estados.append(r.tem_fogo)
        if t >= n - ultimos:
            detec.append(r.tem_fogo)
            confs.append(r.confianca)
    taxa = 100.0 * sum(detec) / len(detec)
    # Estabilidade: nº de vezes que o estado tem_fogo trocou no trecho todo.
    trocas = sum(1 for i in range(1, len(estados)) if estados[i] != estados[i - 1])
    print(f"{nome:34s} deteccao_ult{ultimos}={taxa:5.1f}%  "
          f"conf_med={np.mean(confs):.2f}  conf_pico={max(confs):.2f}  trocas={trocas}")
    return taxa, trocas


def rodar_samples():
    """Folhas reais como sequência: não pode virar fogo."""
    pasta = os.path.join(config.ROOT_DIR, "assets", "samples")
    arqs = sorted(f for f in os.listdir(pasta)
                  if f.lower().endswith((".jpg", ".jpeg", ".png")))
    det = DetectorFogo(conf_threshold=config.FOGO_CONF_THRESHOLD)
    n_fogo = 0
    for nome in arqs:
        img = cv2.imread(os.path.join(pasta, nome))
        img = cv2.resize(img, (W, H))
        # passa o mesmo frame 2x pra dar histórico de cintilação
        det.analisar(img)
        r = det.analisar(img)
        if r.tem_fogo:
            n_fogo += 1
            print(f"   !! FALSO POSITIVO em {nome}: conf={r.confianca:.2f}")
    print(f"{'folhas reais (samples)':34s} falsos_positivos={n_fogo}/{len(arqs)}")
    return n_fogo


if __name__ == "__main__":
    print(f"Limite de alerta de fogo: conf >= {config.FOGO_CONF_THRESHOLD}\n")
    taxa_fogo, trocas_fogo = rodar("chama sintetica (com flicker)", frame_chama)
    taxa_sol, _ = rodar("laranja estatico (por do sol)", frame_laranja_estatico)
    fp_folhas = rodar_samples()

    print("\nResumo:")
    ok_fogo = taxa_fogo >= 80
    ok_estavel = trocas_fogo <= 2          # estabilidade: quase sem piscar
    ok_sol = taxa_sol <= 10
    ok_folhas = fp_folhas == 0
    print(f"  [{'OK' if ok_fogo else 'XX'}] detecta chama sintetica ({taxa_fogo:.0f}%)")
    print(f"  [{'OK' if ok_estavel else 'XX'}] estavel (sem piscar): {trocas_fogo} trocas de estado")
    print(f"  [{'OK' if ok_sol else 'XX'}] rejeita laranja estatico ({taxa_sol:.0f}%)")
    print(f"  [{'OK' if ok_folhas else 'XX'}] rejeita folhas verdes ({fp_folhas} FP)")
    sys.exit(0 if (ok_fogo and ok_estavel and ok_sol and ok_folhas) else 1)
