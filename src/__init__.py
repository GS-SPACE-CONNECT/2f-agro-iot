"""
2F-AGRO · Olho na Folha — pacote de visão computacional.

Módulos:
    config      — constantes, threshold e mapa de classes (PT-BR).
    classifier  — wrapper do modelo YOLOv8-cls (carrega + infere).
    camera      — fonte de frames (webcam / vídeo / imagens) resiliente.
    overlay     — desenho de classe, confiança e FPS sobre o frame.
    api_client  — envio do diagnóstico pra API com fila offline.
"""

__version__ = "1.0.0"
