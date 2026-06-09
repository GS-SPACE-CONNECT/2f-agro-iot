#!/usr/bin/env python3
"""
Prepara o dataset de classificação a partir do PlantVillage.

Pega as 6 pastas de origem do PlantVillage (nomes longos tipo
`Tomato___Bacterial_spot`), renomeia pras nossas chaves limpas
(`mancha_bacteriana_tomate`, ...), balanceia (cap por classe) e divide em
train/val no formato que o Ultralytics-cls espera (ImageFolder):

    data/folha-cls/
        train/<classe>/*.jpg
        val/<classe>/*.jpg

Uso:
    python train/prepare_dataset.py \
        --src ~/dev/pv/raw/color \
        --out data/folha-cls \
        --max-per-class 600 --val-split 0.2
"""
from __future__ import annotations

import argparse
import os
import random
import shutil

# PlantVillage (pasta de origem) -> chave limpa usada pelo modelo/HUD.
SOURCE_TO_KEY = {
    "Tomato___Bacterial_spot": "mancha_bacteriana_tomate",
    "Tomato___Late_blight": "requeima_tomate",
    "Squash___Powdery_mildew": "oidio_mofo_branco",
    "Grape___Black_rot": "podridao_negra_uva",
    "Corn_(maize)___Common_rust_": "ferrugem_milho",
    "Tomato___healthy": "saudavel",
}

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp")


def parse_args() -> argparse.Namespace:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = argparse.ArgumentParser(description="Prepara PlantVillage -> dataset cls.")
    p.add_argument("--src", default=os.path.expanduser("~/dev/pv/raw/color"),
                   help="Raiz com as pastas de classes do PlantVillage.")
    p.add_argument("--out", default=os.path.join(here, "data", "folha-cls"),
                   help="Saida do dataset preparado (train/ e val/).")
    p.add_argument("--max-per-class", type=int, default=600,
                   help="Maximo de imagens por classe (balanceia + acelera CPU).")
    p.add_argument("--val-split", type=float, default=0.2, help="Fracao de validacao.")
    p.add_argument("--seed", type=int, default=42, help="Semente do shuffle.")
    return p.parse_args()


def listar_imagens(pasta: str) -> list[str]:
    return [os.path.join(pasta, f) for f in os.listdir(pasta)
            if f.lower().endswith(IMG_EXTS)]


def main() -> int:
    args = parse_args()
    random.seed(args.seed)

    if not os.path.isdir(args.src):
        print(f"[ERRO] Pasta de origem nao existe: {args.src}\n"
              "       Baixe o PlantVillage antes (ver README / HANDOFF).")
        return 2

    # Limpa saída anterior pra evitar mistura.
    if os.path.exists(args.out):
        shutil.rmtree(args.out)

    total_train = total_val = 0
    print(f"{'classe':28s} {'train':>6s} {'val':>5s}")
    print("-" * 42)
    faltando = []
    for origem, chave in SOURCE_TO_KEY.items():
        pasta = os.path.join(args.src, origem)
        if not os.path.isdir(pasta):
            faltando.append(origem)
            continue

        imgs = listar_imagens(pasta)
        random.shuffle(imgs)
        imgs = imgs[: args.max_per_class]

        n_val = int(len(imgs) * args.val_split)
        val_imgs, train_imgs = imgs[:n_val], imgs[n_val:]

        for split, conjunto in (("train", train_imgs), ("val", val_imgs)):
            destino = os.path.join(args.out, split, chave)
            os.makedirs(destino, exist_ok=True)
            for src_path in conjunto:
                nome = os.path.basename(src_path)
                shutil.copy2(src_path, os.path.join(destino, nome))

        total_train += len(train_imgs)
        total_val += len(val_imgs)
        print(f"{chave:28s} {len(train_imgs):6d} {len(val_imgs):5d}")

    print("-" * 42)
    print(f"{'TOTAL':28s} {total_train:6d} {total_val:5d}")
    print(f"\n[OK] Dataset preparado em: {args.out}")

    if faltando:
        print(f"[AVISO] Pastas de origem nao encontradas: {faltando}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
