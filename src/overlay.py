"""
Desenho do HUD sobre o frame: classe prevista, confiança, FPS e status.

Decisão técnica: usamos SOMENTE OpenCV (sem PIL/TTF) e rótulos em ASCII-limpo.
O motivo é robustez — `cv2.putText` com fonte Hershey não renderiza acentos nem
emoji, então mantemos o texto da tela sem acento (os acentos/emoji vivem nos logs
e no README). Isso faz o overlay funcionar igual em qualquer máquina, sem depender
de fontes instaladas. (Rubrica: "FPS visível" + robustez.)
"""
from __future__ import annotations

import cv2
import numpy as np

# Paleta (BGR)
_VERDE = (90, 200, 90)
_VERMELHO = (60, 60, 230)
_AMARELO = (50, 200, 240)
_BRANCO = (245, 245, 245)
_PRETO = (20, 20, 20)

_FONTE = cv2.FONT_HERSHEY_SIMPLEX


def _banner(frame: np.ndarray, x1: int, y1: int, x2: int, y2: int,
            cor=_PRETO, alpha: float = 0.55) -> None:
    """Desenha um retângulo semitransparente in-place (fundo do HUD)."""
    sub = frame[y1:y2, x1:x2]
    if sub.size == 0:
        return
    cor_layer = np.full(sub.shape, cor, dtype=np.uint8)
    cv2.addWeighted(cor_layer, alpha, sub, 1 - alpha, 0, sub)


def desenhar_hud(frame: np.ndarray, label: str, conf: float, fps: float,
                 saudavel: bool, enviando: bool = False) -> np.ndarray:
    """
    Sobrepõe o HUD ao frame e devolve o mesmo frame (modificado in-place).

    Args:
        frame: imagem BGR (numpy) vinda do OpenCV.
        label: rótulo PT-BR (ASCII) da classe prevista.
        conf: confiança 0..1.
        fps: quadros por segundo atuais.
        saudavel: True pinta o status de verde; False de vermelho.
        enviando: True mostra um marcador de "enviado pra API".
    """
    h, w = frame.shape[:2]
    cor_status = _VERDE if saudavel else _VERMELHO

    # ---- Banner superior (classe + confiança) ----
    _banner(frame, 0, 0, w, 78)

    # Bolinha de status
    cv2.circle(frame, (28, 39), 12, cor_status, -1)
    cv2.circle(frame, (28, 39), 12, _BRANCO, 1, cv2.LINE_AA)

    # Rótulo da classe
    cv2.putText(frame, label, (52, 34), _FONTE, 0.8, _BRANCO, 2, cv2.LINE_AA)

    # Linha de confiança + barra
    pct = int(round(conf * 100))
    cv2.putText(frame, f"Conf: {pct}%", (52, 62), _FONTE, 0.6, _BRANCO, 1,
                cv2.LINE_AA)
    bar_x, bar_y, bar_w = 175, 52, 180
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 12),
                  (70, 70, 70), -1)
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + int(bar_w * max(0.0, min(1.0, conf))), bar_y + 12),
                  cor_status, -1)

    # ---- FPS (canto superior direito) ----
    fps_txt = f"FPS: {fps:4.1f}"
    (tw, _), _ = cv2.getTextSize(fps_txt, _FONTE, 0.7, 2)
    cv2.putText(frame, fps_txt, (w - tw - 16, 34), _FONTE, 0.7, _AMARELO, 2,
                cv2.LINE_AA)

    # Marcador de envio pra API
    if enviando:
        cv2.putText(frame, "API <<", (w - 120, 64), _FONTE, 0.6, _VERDE, 2,
                    cv2.LINE_AA)

    # ---- Rodapé (marca do projeto + ajuda) ----
    _banner(frame, 0, h - 30, w, h)
    cv2.putText(frame, "2F-AGRO - Olho na Folha", (12, h - 10), _FONTE, 0.55,
                _BRANCO, 1, cv2.LINE_AA)
    ajuda = "[q] sair"
    (aw, _), _ = cv2.getTextSize(ajuda, _FONTE, 0.55, 1)
    cv2.putText(frame, ajuda, (w - aw - 12, h - 10), _FONTE, 0.55, _BRANCO, 1,
                cv2.LINE_AA)

    return frame


def desenhar_erro(frame: np.ndarray, mensagem: str) -> np.ndarray:
    """HUD mínimo de erro (ex.: frame inválido) — nunca deixa a tela 'muda'."""
    h, w = frame.shape[:2]
    _banner(frame, 0, 0, w, 40, cor=_VERMELHO, alpha=0.6)
    cv2.putText(frame, mensagem[:60], (12, 27), _FONTE, 0.6, _BRANCO, 2,
                cv2.LINE_AA)
    return frame
