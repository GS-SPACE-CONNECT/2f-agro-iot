#!/usr/bin/env python3
"""
Treina o YOLOv8-cls do Olho na Folha sobre o dataset preparado.

Fine-tuning do `yolov8n-cls.pt` (pré-treinado em ImageNet) nas 6 classes do 2F-AGRO.
Funciona em CPU (mais lento) ou GPU/Colab (`--device 0`). Ao final, copia o melhor
checkpoint pra `models/2fagro-folha-cls-v1.pt`, que é o que o script da webcam usa.

Uso:
    python train/train.py                       # CPU, padrões
    python train/train.py --device 0 --epochs 40  # GPU (Colab)
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil


def parse_args() -> argparse.Namespace:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = argparse.ArgumentParser(description="Treina YOLOv8-cls (Olho na Folha).")
    p.add_argument("--data", default=os.path.join(here, "data", "folha-cls"),
                   help="Dataset cls (pastas train/ e val/).")
    p.add_argument("--model", default="yolov8n-cls.pt",
                   help="Modelo base pra fine-tuning.")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--imgsz", type=int, default=224)
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--device", default="cpu", help="'cpu' ou '0' (GPU).")
    p.add_argument("--out", default=os.path.join(here, "models",
                                                 "2fagro-folha-cls-v1.pt"))
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not os.path.isdir(os.path.join(args.data, "train")):
        print(f"[ERRO] Dataset nao encontrado em {args.data}.\n"
              "       Rode antes: python train/prepare_dataset.py")
        return 2

    try:
        from ultralytics import YOLO
    except ImportError:
        print("[ERRO] Ultralytics nao instalado. pip install -r requirements.txt")
        return 2

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"[INFO] Treinando {args.model} | data={args.data} | epochs={args.epochs} "
          f"| imgsz={args.imgsz} | batch={args.batch} | device={args.device}")

    model = YOLO(args.model)
    resultados = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=os.path.join(here, "runs"),
        name="folha-cls",
        exist_ok=True,
        patience=8,           # early stop se não melhorar
        seed=42,
        verbose=True,
    )

    # Localiza o best.pt (robusto a variações de versão do Ultralytics).
    best = None
    try:
        best = os.path.join(str(resultados.save_dir), "weights", "best.pt")
    except Exception:
        best = None
    if not best or not os.path.exists(best):
        candidatos = glob.glob(os.path.join(here, "runs", "**", "weights", "best.pt"),
                               recursive=True)
        best = max(candidatos, key=os.path.getmtime) if candidatos else None

    if not best or not os.path.exists(best):
        print("[ERRO] Nao encontrei o best.pt apos o treino.")
        return 3

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    shutil.copy2(best, args.out)
    print(f"\n[OK] Modelo salvo em: {args.out}")

    # Validação final — mostra acurácia top-1/top-5.
    try:
        metrics = model.val(data=args.data, imgsz=args.imgsz, device=args.device)
        top1 = getattr(metrics, "top1", None)
        top5 = getattr(metrics, "top5", None)
        if top1 is not None:
            print(f"[METRICAS] top1={top1:.4f}  top5={top5:.4f}")
    except Exception as e:
        print(f"[AVISO] Validacao final falhou (nao critico): {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
