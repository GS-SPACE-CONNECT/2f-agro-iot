# 📷 2f-agro-iot

> Visão computacional do 2F-AGRO — **"Olho na Folha"** detecta pragas via webcam.
> Matéria: **IoT / Physical Computing** (100 pts) · FIAP 3ES · GS 2026.1

[![Hub](https://img.shields.io/badge/hub-2f--agro-success)](https://github.com/GS-SPACE-CONNECT/2f-agro)

## 🎯 Objetivo
Script Python com YOLOv8 + OpenCV detectando pragas e doenças em folhas via webcam em tempo real. Integra com o app mobile.

## 👥 Owners
[@jota0802](https://github.com/jota0802), [@lucksza](https://github.com/lucksza) · Team [`iot-cv`](https://github.com/orgs/GS-SPACE-CONNECT/teams/iot-cv)

## 📦 Entregáveis (100 pts)
- **Vídeo da solução** (50 pts) — demo + arquitetura + FPS visível
- **Script Python** (30 pts) — modularizado + tratamento de exceções **obrigatório**
- **Repositório Git** (20 pts) — este repo + `requirements.txt` + README

## 🌿 Pragas alvo
🍅 Mancha bacteriana do tomate · 🌽 Lagarta-do-cartucho · ☕ Ferrugem do café · 🥬 Mofo branco / Oídio · 🍇 Míldio

## 📚 Datasets de treino
- [PlantVillage](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset) (38 classes, ~50k imagens)
- [PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset) (fotos reais de campo)

## 🧩 Stack
Python 3.10+ · Ultralytics YOLOv8 · OpenCV · Pillow · (opcional) ONNX

## 🚀 Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python olho_na_folha.py
```

## ⚠️ Robustez exigida (rubrica)
- ✅ Tratamento de exceções no stream
- ✅ FPS visível na tela
- ✅ Robustez a iluminação variável e oclusão parcial
- ✅ `requirements.txt` com versões fixas

## 🔗 Links
- [Spec § 4.2 IoT/CV](https://github.com/GS-SPACE-CONNECT/2f-agro/blob/main/docs/specs/2026-05-27-2f-agro-design.md)
- [App Mobile (integração)](https://github.com/GS-SPACE-CONNECT/2f-agro-mobile)
