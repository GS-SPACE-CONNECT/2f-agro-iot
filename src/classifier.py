"""
Wrapper do modelo YOLOv8-cls (Ultralytics).

Isola toda a dependência de ML num só lugar: carrega o modelo treinado do 2F-AGRO
(`models/2fagro-folha-cls-v1.pt`) e, se ele ainda não existir, cai pro `yolov8n-cls.pt`
base — assim dá pra testar o pipeline de vídeo ANTES de o treino terminar.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Predicao:
    """Resultado de uma inferência de classificação."""
    classe: str           # chave da classe (ex.: 'ferrugem_milho')
    confianca: float      # 0..1
    top5: list            # [(classe, conf), ...] — útil pra debug/HUD


class ModeloIndisponivel(RuntimeError):
    """Erro claro quando o modelo não pôde ser carregado."""


class Classificador:
    """Carrega o YOLOv8-cls e classifica frames."""

    def __init__(self, model_path: str, fallback_model: str = "yolov8n-cls.pt",
                 imgsz: int = 224):
        self.imgsz = imgsz
        try:
            from ultralytics import YOLO  # import tardio: só quando vai usar
        except ImportError as e:
            raise ModeloIndisponivel(
                "Ultralytics nao instalado. Rode: pip install -r requirements.txt"
            ) from e

        caminho = model_path
        self.usando_fallback = False
        if not os.path.exists(model_path):
            # Sem modelo treinado ainda: usa o base (ImageNet) só pra não travar.
            caminho = fallback_model
            self.usando_fallback = True

        try:
            self.model = YOLO(caminho)
        except Exception as e:
            raise ModeloIndisponivel(
                f"Falha ao carregar o modelo '{caminho}': {e}"
            ) from e

        self.nomes = self.model.names  # {idx: 'classe'}

    def aquecer(self) -> None:
        """Roda uma inferência dummy pra carregar pesos (1ª real fica rápida)."""
        try:
            import numpy as np
            dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype="uint8")
            self.model.predict(dummy, imgsz=self.imgsz, verbose=False)
        except Exception:
            pass  # warmup é best-effort; nunca é fatal

    def prever(self, frame) -> Predicao:
        """
        Classifica um frame BGR (numpy). Retorna a classe top-1 + confiança.
        Lança ModeloIndisponivel apenas em erro irrecuperável de inferência —
        o chamador decide se ignora o frame (stream não pode cair por 1 frame ruim).
        """
        try:
            resultados = self.model.predict(frame, imgsz=self.imgsz, verbose=False)
        except Exception as e:
            raise ModeloIndisponivel(f"Erro de inferencia: {e}") from e

        r = resultados[0]
        probs = getattr(r, "probs", None)
        if probs is None:
            # Modelo não-classificação carregado por engano.
            raise ModeloIndisponivel(
                "Modelo carregado nao e de classificacao (sem .probs)."
            )

        idx_top1 = int(probs.top1)
        conf_top1 = float(probs.top1conf)
        classe = self.nomes.get(idx_top1, str(idx_top1))

        top5 = []
        try:
            for idx, conf in zip(list(probs.top5), list(probs.top5conf)):
                top5.append((self.nomes.get(int(idx), str(int(idx))), float(conf)))
        except Exception:
            top5 = [(classe, conf_top1)]

        return Predicao(classe=classe, confianca=conf_top1, top5=top5)
