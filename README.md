# 2f-agro-iot

Visao computacional do 2F-AGRO - **Olho na Folha** detecta pragas via webcam.
Materia: **IoT / Physical Computing** (100 pts) | FIAP 3ES | GS 2026.1

[![Hub](https://img.shields.io/badge/hub-2f--agro-success)](https://github.com/GS-SPACE-CONNECT/2f-agro)

## Objetivo
Script Python com YOLOv8 + OpenCV detectando pragas e doencas em folhas via webcam em tempo real. Integra com app mobile.

## Owners
[@jota0802](https://github.com/jota0802), [@lucksza](https://github.com/lucksza) | Team [`iot-cv`](https://github.com/orgs/GS-SPACE-CONNECT/teams/iot-cv)

## Entregaveis (100 pts)
- Video da solucao (50 pts) - demo + arquitetura + FPS visivel
- Script Python (30 pts) - modularizado + tratamento de excecoes OBRIGATORIO
- Repositorio Git (20 pts) - este repo + requirements.txt + README

## Pragas alvo
Mancha bacteriana tomate | Lagarta-do-cartucho | Ferrugem do cafe | Mofo branco/Oidio | Mildio

## Datasets de treino
- [PlantVillage](https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset)
- [PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset)

## Stack
Python 3.10+ | Ultralytics YOLOv8 | OpenCV | Pillow | (opcional) ONNX

## Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python olho_na_folha.py

## Robustez (rubrica)
- Tratamento de excecoes no stream
- FPS visivel
- Robustez a iluminacao e oclusao
- requirements.txt com versoes fixas

## Links
- [Spec IoT/CV](https://github.com/GS-SPACE-CONNECT/2f-agro/blob/main/docs/specs/2026-05-27-2f-agro-design.md)
- [Mobile](https://github.com/GS-SPACE-CONNECT/2f-agro-mobile)
