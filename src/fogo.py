"""
Detector de fogo/queimada por heurística (sem ML) — modo complementar do Olho na Folha.

Por que heurística e não um modelo: queimada na lavoura é uma ameaça real pro
pequeno agricultor (especialmente no semiárido), e o tema da GS é justamente
monitoramento de desastres por satélite (cf. INPE Programa Queimadas / Charter
Space and Major Disasters). Como complemento à detecção de pragas, uma heurística
de visão roda em qualquer máquina, sem treino nem download de pesos — ideal pra
edge barato (Raspberry) e pra demo.

Sinais por frame (combinados pra cortar falso positivo):
  1. COR       — pixel de chama é quente (vermelho/laranja/amarelo), saturado e
                 brilhante. Cruzamos um teste HSV com um teste BGR (R dominante).
  2. ÁREA      — a região quente precisa de tamanho mínimo (corta reflexo/ruído).
  3. CINTILAÇÃO— a chama "treme": a máscara muda de um frame pro outro. Pôr do sol,
                 lâmpada e roupa laranja são ESTÁTICOS → reprovam aqui.
  4. NÚCLEO    — chama de verdade tem miolo branco-quente (V altíssimo). Mede a
                 "qualidade" da cor e ajuda a confiança a subir com fogo nítido.

ESTABILIDADE (o ponto-chave): decidir frame a frame faz o indicador "piscar" e a
confiança pular. Por isso o detector tem MEMÓRIA TEMPORAL:
  • a confiança é suavizada por média móvel exponencial (EMA) — sobe e desce
    gradualmente, sem tremer;
  • o liga/desliga usa HISTERESE (liga num limiar alto, só desliga num limiar bem
    mais baixo) — uma vez "FOGO", segura o estado e não fica piscando na borda;
  • fogo sustentado ganha um bônus de persistência — a confiança sobe rumo a ~95%
    quando a chama fica firme por ~1 s, em vez de saltar.

Importante: a cintilação é um PORTÃO — sem movimento não é fogo. Logo o modo
funciona em fonte ao vivo (webcam) ou vídeo; uma foto PARADA de chama não é
distinguível de um pôr do sol e, de propósito, não dispara.

Robustez (rubrica): nunca lança por um frame ruim — em qualquer erro mantém o
estado anterior e segue o stream.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np


@dataclass
class DeteccaoFogo:
    """Resultado da análise de fogo de um frame (já suavizado no tempo)."""
    tem_fogo: bool
    confianca: float                 # 0..1 — confiança SUAVIZADA (estável)
    area_frac: float                 # fração da tela coberta por chama
    flicker: float                   # 0..1 — cintilação suavizada
    bbox: tuple | None = None        # (x, y, w, h) da maior região, ou None
    contornos: list = field(default_factory=list)


class DetectorFogo:
    """Detector heurístico de fogo, estável no tempo (EMA + histerese)."""

    def __init__(
        self,
        conf_threshold: float = 0.55,      # limiar pra LIGAR o alerta
        conf_desliga: float = 0.30,        # limiar (mais baixo) pra DESLIGAR — histerese
        area_min_frac: float = 0.0025,     # ~0,25% da tela já conta (chama pequena)
        ema_alpha: float = 0.35,           # peso do frame atual na suavização (0..1)
        area_tau: float = 0.010,           # 'velocidade' da curva de área (chama pequena pontua)
        flicker_norm: float = 0.35,        # cintilação que já vale nota máxima
        flicker_gate: float = 0.08,        # cintilação mínima (suave) pra valer como fogo
        historico: int = 12,
    ):
        self.conf_threshold = conf_threshold
        self.conf_desliga = min(conf_desliga, conf_threshold)
        self.area_min_frac = area_min_frac
        self.ema_alpha = ema_alpha
        self.area_tau = area_tau
        self.flicker_norm = flicker_norm
        self.flicker_gate = flicker_gate
        self._mascaras = deque(maxlen=historico)

        # Estado temporal (a "memória" que dá estabilidade).
        self._conf_ema = None     # confiança suavizada (None = ainda não iniciada)
        self._flicker_ema = 0.0   # cintilação suavizada (só pra exibir bonito)
        self._tem_fogo = False    # estado com histerese
        self._streak = 0          # frames seguidos de fogo forte (persistência)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _mascara_fogo(hsv: np.ndarray, frame_bgr: np.ndarray) -> np.ndarray:
        """Máscara binária dos pixels com 'cara' de chama (cor quente e brilhante)."""
        # Tons quentes (vermelho->amarelo), saturados e brilhantes. H "dá a volta"
        # no vermelho, daí as duas faixas.
        quente_a = cv2.inRange(hsv, (0, 90, 170), (25, 255, 255))
        quente_b = cv2.inRange(hsv, (160, 90, 170), (179, 255, 255))
        # Núcleo branco-quente da chama: brilho altíssimo, saturação baixa.
        nucleo = cv2.inRange(hsv, (0, 0, 240), (179, 90, 255))
        mask_hsv = cv2.bitwise_or(cv2.bitwise_or(quente_a, quente_b), nucleo)

        # Reforço em BGR: chama tem R dominante (R > G > B) e R alto.
        b, g, r = cv2.split(frame_bgr.astype(np.int16))
        mask_bgr = ((r > 140) & (r >= g + 12) & (g >= b)).astype(np.uint8) * 255

        mask = cv2.bitwise_and(mask_hsv, mask_bgr)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)
        return mask

    @staticmethod
    def _maior_bbox(mask: np.ndarray):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            return None, []
        maior = max(cnts, key=cv2.contourArea)
        return cv2.boundingRect(maior), cnts

    def _flicker(self, mask: np.ndarray) -> float:
        """'Tremor' = diferença simétrica com a máscara anterior, normalizada (0..1)."""
        if not self._mascaras:
            return 0.0
        anterior = self._mascaras[-1]
        if anterior.shape != mask.shape:
            return 0.0
        area_diff = int(np.count_nonzero(cv2.bitwise_xor(mask, anterior)))
        area_media = (int(np.count_nonzero(mask)) +
                      int(np.count_nonzero(anterior))) / 2.0
        if area_media < 1:
            return 0.0
        return float(min(1.0, area_diff / area_media))

    @staticmethod
    def _qualidade_nucleo(hsv: np.ndarray, mask: np.ndarray) -> float:
        """Fração da máscara que é miolo bem brilhante (V alto), normalizada (0..1).

        Chama real tem bastante núcleo branco-quente; um reflexo laranja fosco quase
        não tem. Bom tanto pra confiança quanto pra precisão.
        """
        n = int(np.count_nonzero(mask))
        if n == 0:
            return 0.0
        v = hsv[:, :, 2]
        brilhantes = int(np.count_nonzero((mask > 0) & (v >= 205)))
        return float(min(1.0, (brilhantes / n) / 0.12))

    # ------------------------------------------------------------------ #
    def analisar(self, frame_bgr: np.ndarray) -> DeteccaoFogo:
        try:
            return self._analisar(frame_bgr)
        except Exception:
            # Robustez: frame ruim não derruba o stream — devolve o estado atual.
            return DeteccaoFogo(self._tem_fogo, round(self._conf_ema or 0.0, 4),
                                0.0, round(self._flicker_ema, 4))

    def _analisar(self, frame_bgr: np.ndarray) -> DeteccaoFogo:
        h, w = frame_bgr.shape[:2]
        total = float(h * w)
        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = self._mascara_fogo(hsv, frame_bgr)
        area_frac = float(np.count_nonzero(mask)) / total if total else 0.0

        flicker = self._flicker(mask)
        self._mascaras.append(mask)

        bbox, cnts = self._maior_bbox(mask)
        qualidade = self._qualidade_nucleo(hsv, mask)

        # Cintilação suavizada (estável) — usada como PORTÃO de movimento.
        a = self.ema_alpha
        self._flicker_ema = a * flicker + (1 - a) * self._flicker_ema

        # --- Score instantâneo (0..1): cor/área + cintilação + núcleo ---
        # Área satura suave: ~1% já vale bastante (chama de vela é pequena).
        area_score = 1.0 - math.exp(-area_frac / self.area_tau)
        flicker_score = min(1.0, flicker / self.flicker_norm)
        # PORTÃO de movimento: sem cintilação sustentada NÃO é fogo, por mais quente
        # e grande que seja a mancha (corta pôr do sol / laranja parado). É suave
        # (usa a cintilação já suavizada), então não reintroduz o "piscar".
        fator_mov = min(1.0, self._flicker_ema / self.flicker_gate)

        if area_frac < self.area_min_frac:
            score_inst = 0.0
        else:
            base = 0.45 * area_score + 0.30 * flicker_score + 0.25 * qualidade
            score_inst = fator_mov * base

        # --- Suavização temporal (EMA) da confiança — o que mata o "piscar" ---
        self._conf_ema = score_inst if self._conf_ema is None \
            else a * score_inst + (1 - a) * self._conf_ema

        # --- Persistência: fogo firme empurra a confiança rumo a ~95% ---
        if score_inst >= self.conf_threshold:
            self._streak = min(self._streak + 1, 30)
        else:
            self._streak = max(self._streak - 2, 0)
        boost = 0.18 * (self._streak / 30.0)
        confianca = min(0.99, self._conf_ema + boost)

        # --- Histerese: liga alto, só desliga bem mais baixo ---
        if self._tem_fogo:
            self._tem_fogo = confianca >= self.conf_desliga
        else:
            self._tem_fogo = confianca >= self.conf_threshold

        if bbox is not None and area_frac < self.area_min_frac:
            bbox = None

        return DeteccaoFogo(
            tem_fogo=self._tem_fogo,
            confianca=round(confianca, 4),
            area_frac=round(area_frac, 5),
            flicker=round(self._flicker_ema, 4),
            bbox=bbox,
            contornos=cnts,
        )
