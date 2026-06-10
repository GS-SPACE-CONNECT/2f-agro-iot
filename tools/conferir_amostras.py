"""Mostra, imagem por imagem: classe verdadeira (do nome do arquivo) x previsao do modelo.

Serve pra ENTENDER como o modelo "confirma" uma praga: rodamos as amostras cuja
resposta certa ja conhecemos e comparamos com o que ele preve, com a confianca.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from src import config
from src.classifier import Classificador
from src.config import info_classe

PASTA = os.path.join(config.ROOT_DIR, "assets", "samples")

clf = Classificador(config.MODEL_PATH, config.FALLBACK_MODEL, config.IMG_SIZE)
clf.aquecer()
print(f"Modelo: {'FALLBACK ImageNet' if clf.usando_fallback else os.path.basename(config.MODEL_PATH)}")
print(f"Limite de alerta: confianca >= {config.CONF_THRESHOLD*100:.0f}%\n")

arquivos = sorted(f for f in os.listdir(PASTA) if f.lower().endswith((".jpg", ".jpeg", ".png")))
acertos = 0
for nome in arquivos:
    verdadeiro = re.sub(r"_\d+$", "", os.path.splitext(nome)[0])  # tira o "_1"/"_2"
    frame = cv2.imread(os.path.join(PASTA, nome))
    pred = clf.prever(frame)
    info = info_classe(pred.classe)
    ok = "OK " if pred.classe == verdadeiro else "XX "
    if pred.classe == verdadeiro:
        acertos += 1
    alerta = "ALERTA" if (pred.confianca >= config.CONF_THRESHOLD and not info.saudavel) else "ok/sadia"
    print(f"{ok} {nome:32s} real={verdadeiro:26s} -> previu={pred.classe:26s} "
          f"conf={pred.confianca*100:5.1f}%  [{alerta}]")

print(f"\nAcertos: {acertos}/{len(arquivos)}")
