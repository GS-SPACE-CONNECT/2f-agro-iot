"""
Desenho do HUD sobre o frame: classe prevista, confiança, FPS e status.

Decisão técnica: usamos SOMENTE OpenCV (sem PIL/TTF) e rótulos em ASCII-limpo.
O motivo é robustez — `cv2.putText` com fonte Hershey não renderiza acentos nem
emoji, então mantemos o texto da tela sem acento (os acentos/emoji vivem nos logs
e no README). Isso faz o overlay funcionar igual em qualquer máquina, sem depender
de fontes instaladas. (Rubrica: "FPS visível" + robustez.)

O HUD é **adaptativo**: todas as fontes, posições e a barra de confiança escalam
com a largura do frame, então fica legível tanto numa webcam 1280px quanto numa
imagem de amostra 256px (sem texto sobreposto).
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
    x1, y1 = max(0, x1), max(0, y1)
    sub = frame[y1:y2, x1:x2]
    if sub.size == 0:
        return
    cor_layer = np.full(sub.shape, cor, dtype=np.uint8)
    cv2.addWeighted(cor_layer, alpha, sub, 1 - alpha, 0, sub)


def _truncar(texto: str, fs: float, th: int, max_w: int) -> str:
    """Encurta o texto (com '..') pra caber em max_w pixels."""
    if max_w <= 0:
        return ""
    (w, _), _ = cv2.getTextSize(texto, _FONTE, fs, th)
    if w <= max_w:
        return texto
    while texto and cv2.getTextSize(texto + "..", _FONTE, fs, th)[0][0] > max_w:
        texto = texto[:-1]
    return (texto + "..") if texto else ""


def desenhar_hud(frame: np.ndarray, label: str, conf: float, fps: float,
                 saudavel: bool, enviando: bool = False) -> np.ndarray:
    """
    Sobrepõe o HUD ao frame e devolve o mesmo frame (modificado in-place).
    Tudo escala com a largura, então não há texto sobreposto em frame pequeno.
    """
    h, w = frame.shape[:2]
    s = max(0.5, min(w / 640.0, 2.2))      # fator de escala pela largura
    cor_status = _VERDE if saudavel else _VERMELHO

    banner_h = int(70 * s)
    pad = int(14 * s)
    fs_label = 0.7 * s
    fs_small = 0.52 * s
    th = max(1, int(round(2 * s)))
    th1 = max(1, int(round(1.2 * s)))
    y1 = int(banner_h * 0.45)              # linha 1 (label / fps)
    y2 = int(banner_h * 0.82)              # linha 2 (conf / api)

    _banner(frame, 0, 0, w, banner_h)

    # ---- FPS no canto direito (desenhado 1º pra reservar o espaço) ----
    fps_txt = f"FPS: {fps:4.1f}"
    (fw, _), _ = cv2.getTextSize(fps_txt, _FONTE, fs_small, th)
    fps_x = w - fw - pad
    cv2.putText(frame, fps_txt, (fps_x, y1), _FONTE, fs_small, _AMARELO, th, cv2.LINE_AA)
    if enviando:
        api_txt = "API <<"
        (aw, _), _ = cv2.getTextSize(api_txt, _FONTE, fs_small, th1)
        cv2.putText(frame, api_txt, (w - aw - pad, y2), _FONTE, fs_small, _VERDE,
                    th1, cv2.LINE_AA)

    # ---- Status + rótulo (truncado pra não bater no FPS) ----
    cx = pad + int(10 * s)
    cv2.circle(frame, (cx, y1 - int(6 * s)), int(10 * s), cor_status, -1)
    cv2.circle(frame, (cx, y1 - int(6 * s)), int(10 * s), _BRANCO, th1, cv2.LINE_AA)
    label_x = cx + int(18 * s)
    label_fit = _truncar(label, fs_label, th, fps_x - label_x - int(8 * s))
    cv2.putText(frame, label_fit, (label_x, y1), _FONTE, fs_label, _BRANCO, th,
                cv2.LINE_AA)

    # ---- Confiança: texto + barra (linha 2) ----
    pct = int(round(conf * 100))
    conf_txt = f"Conf: {pct}%"
    cv2.putText(frame, conf_txt, (label_x, y2), _FONTE, fs_small, _BRANCO, th1,
                cv2.LINE_AA)
    (cw, _), _ = cv2.getTextSize(conf_txt, _FONTE, fs_small, th1)
    bar_x = label_x + cw + int(10 * s)
    bar_y = int(banner_h * 0.62)
    bar_h = int(12 * s)
    bar_w = max(int(50 * s), min(int(220 * s), fps_x - bar_x - int(10 * s)))
    if bar_w > 0:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
                      (70, 70, 70), -1)
        prog = int(bar_w * max(0.0, min(1.0, conf)))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + prog, bar_y + bar_h),
                      cor_status, -1)

    # ---- Rodapé: marca + ajuda ----
    foot_h = int(26 * s)
    _banner(frame, 0, h - foot_h, w, h)
    fy = h - int(foot_h * 0.3)
    cv2.putText(frame, "2F-AGRO - Olho na Folha", (pad, fy), _FONTE, 0.5 * s,
                _BRANCO, th1, cv2.LINE_AA)
    ajuda = "[q] sair"
    (jw, _), _ = cv2.getTextSize(ajuda, _FONTE, 0.5 * s, th1)
    cv2.putText(frame, ajuda, (w - jw - pad, fy), _FONTE, 0.5 * s, _BRANCO, th1,
                cv2.LINE_AA)

    return frame


def desenhar_erro(frame: np.ndarray, mensagem: str) -> np.ndarray:
    """HUD mínimo de erro (ex.: frame inválido) — nunca deixa a tela 'muda'."""
    h, w = frame.shape[:2]
    s = max(0.5, min(w / 640.0, 2.2))
    _banner(frame, 0, 0, w, int(40 * s), cor=_VERMELHO, alpha=0.6)
    cv2.putText(frame, mensagem[:60], (int(12 * s), int(27 * s)), _FONTE, 0.6 * s,
                _BRANCO, max(1, int(2 * s)), cv2.LINE_AA)
    return frame
