"""
Configuração central do Olho na Folha.

Mantém num só lugar: caminho do modelo, threshold de confiança, endpoint da API
e o mapa de classes (chave técnica do modelo -> rótulo PT-BR amigável). Assim o
resto do código não tem "magic strings" espalhadas (facilita manutenção e revisão).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Caminhos e parâmetros de inferência
# --------------------------------------------------------------------------- #

# Diretório raiz do projeto (este arquivo está em src/).
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modelo treinado (commitado no repo). Se não existir ainda, o classifier cai
# para o yolov8n-cls.pt base — permite testar o pipeline antes do treino.
MODEL_PATH = os.path.join(ROOT_DIR, "models", "2fagro-folha-cls-v1.pt")
FALLBACK_MODEL = "yolov8n-cls.pt"  # baixado pela ultralytics sob demanda

# Resolução de inferência (YOLOv8-cls usa 224 por padrão).
IMG_SIZE = 224

# Confiança mínima pra considerar uma detecção "válida" e mandar pra API.
CONF_THRESHOLD = float(os.getenv("AGRO_CONF_THRESHOLD", "0.70"))

# Endpoint da API de alertas (backend C# .NET). Sobrescreva com a env var.
API_URL = os.getenv("AGRO_API_URL", "http://localhost:5000/api/diagnostico")

# Fila local pra diagnósticos que não conseguiram subir (modo offline).
OFFLINE_QUEUE_PATH = os.path.join(ROOT_DIR, "offline_queue.jsonl")

# Intervalo mínimo (s) entre dois envios da MESMA praga — evita floodar a API.
API_MIN_INTERVAL_S = float(os.getenv("AGRO_API_MIN_INTERVAL_S", "5.0"))

# Nome da janela do OpenCV.
WINDOW_NAME = "2F-AGRO - Olho na Folha"


# --------------------------------------------------------------------------- #
# Mapa de classes
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ClasseFolha:
    """Metadados de exibição de uma classe que o modelo pode prever."""
    label: str          # rótulo curto pra tela (PT-BR)
    emoji: str          # usado em logs/README (NÃO na tela — Hershey não renderiza)
    saudavel: bool      # True = folha sadia, não gera alerta
    descricao: str      # explicação curta pra README/logs


# Chave = nome da classe como o modelo a conhece (= subpasta de treino).
# Mantemos chaves limpas (sem o prefixo gigante do PlantVillage) — ver
# train/prepare_dataset.py, que renomeia as pastas de origem pra estas chaves.
CLASSES: dict[str, ClasseFolha] = {
    "mancha_bacteriana_tomate": ClasseFolha(
        label="Mancha bacteriana (tomate)",
        emoji="🍅",
        saudavel=False,
        descricao="Xanthomonas: pontos escuros encharcados na folha do tomateiro.",
    ),
    "requeima_tomate": ClasseFolha(
        label="Requeima / mildio (tomate)",
        emoji="🍅",
        saudavel=False,
        descricao="Phytophthora infestans: lesoes marrons que alastram rapido.",
    ),
    "oidio_mofo_branco": ClasseFolha(
        label="Oidio / mofo branco",
        emoji="🥬",
        saudavel=False,
        descricao="Powdery mildew: po esbranquicado sobre a superficie foliar.",
    ),
    "podridao_negra_uva": ClasseFolha(
        label="Podridao negra (uva)",
        emoji="🍇",
        saudavel=False,
        descricao="Guignardia bidwellii: manchas necroticas na folha da videira.",
    ),
    "ferrugem_milho": ClasseFolha(
        label="Ferrugem (milho)",
        emoji="🌽",
        saudavel=False,
        descricao="Puccinia sorghi: pustulas alaranjadas/ferrugem na folha do milho.",
    ),
    "saudavel": ClasseFolha(
        label="Folha saudavel",
        emoji="🌿",
        saudavel=True,
        descricao="Sem sinais de praga ou doenca detectados.",
    ),
}

# Ordem canônica das classes (útil pra treino/relatórios).
CLASS_KEYS = list(CLASSES.keys())


def info_classe(nome: str) -> ClasseFolha:
    """
    Retorna os metadados de uma classe prevista pelo modelo.

    Tolerante: se o modelo devolver uma chave desconhecida (ex.: rodando com o
    yolov8n-cls.pt base de ImageNet antes do treino), devolve um ClasseFolha
    genérico em vez de quebrar — robustez exigida pela rubrica.
    """
    classe = CLASSES.get(nome)
    if classe is not None:
        return classe
    return ClasseFolha(
        label=str(nome)[:40],
        emoji="❓",
        saudavel=False,
        descricao="Classe fora do conjunto treinado do 2F-AGRO.",
    )
