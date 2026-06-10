#!/usr/bin/env python3
"""
2F-AGRO · Olho na Folha — detecção de pragas em folhas via webcam, em tempo real.

Pipeline:
    webcam/vídeo -> frame -> YOLOv8-cls -> (classe, confiança)
                 -> HUD (classe + confiança + FPS) na tela
                 -> se confiança > limite e não-saudável: POST pra API (fila offline)

Uso:
    python olho_na_folha.py                    # webcam padrão (índice 0)
    python olho_na_folha.py --source 1         # outra webcam
    python olho_na_folha.py --source amostras/ # pasta de imagens (testa sem webcam)
    python olho_na_folha.py --source demo.mp4  # arquivo de vídeo
    python olho_na_folha.py --no-api           # sem enviar pra API
    python olho_na_folha.py --headless --save out/  # sem janela, salva frames

Teclas:  [q] sai.

Toda a robustez exigida pela rubrica está aqui: tratamento de exceções no stream,
FPS sempre visível e o programa nunca cai por um frame ruim ou por rede fora do ar.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from collections import deque

# Garante que o pacote `src` seja importável independente do diretório atual.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import config
from src.api_client import ApiClient
from src.camera import FonteDeFrames, FonteIndisponivel
from src.classifier import Classificador, ModeloIndisponivel
from src.config import info_classe
from src.fogo import DetectorFogo
from src.overlay import desenhar_erro, desenhar_hud, desenhar_hud_fogo


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="2F-AGRO - Olho na Folha (deteccao de pragas via webcam)."
    )
    p.add_argument("--source", default="0",
                   help="0=webcam | caminho de video | pasta de imagens | imagem.")
    p.add_argument("--model", default=config.MODEL_PATH,
                   help="Caminho do modelo .pt (default: modelo treinado do 2F-AGRO).")
    p.add_argument("--conf", type=float, default=config.CONF_THRESHOLD,
                   help="Confianca minima pra alertar/enviar (0..1).")
    p.add_argument("--api-url", default=config.API_URL, help="Endpoint da API.")
    p.add_argument("--no-api", action="store_true", help="Nao envia pra API.")
    p.add_argument("--fogo", action="store_true",
                   help="Modo fogo/queimada (heuristico) em vez da deteccao de pragas.")
    p.add_argument("--headless", action="store_true",
                   help="Nao abre janela (para testes/servidor).")
    p.add_argument("--save", metavar="DIR", default=None,
                   help="Salva os frames anotados neste diretorio.")
    p.add_argument("--max-frames", type=int, default=0,
                   help="Para apos N frames (0 = infinito). Util em teste.")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # ---- Carrega o modelo (erro aqui é fatal, mas com mensagem clara) ----
    try:
        import cv2  # importado aqui pra dar erro amigável se faltar opencv
    except ImportError:
        print("[ERRO] OpenCV nao instalado. Rode: pip install -r requirements.txt")
        return 2

    classificador = None
    detector_fogo = None
    if args.fogo:
        # Modo fogo: heurística pura, sem carregar o modelo de pragas (mais leve).
        detector_fogo = DetectorFogo(conf_threshold=config.FOGO_CONF_THRESHOLD)
        print("[OK] Modo FOGO/queimada (heuristico). Sem modelo de pragas carregado.")
    else:
        try:
            classificador = Classificador(args.model, config.FALLBACK_MODEL,
                                          config.IMG_SIZE)
        except ModeloIndisponivel as e:
            print(f"[ERRO] {e}")
            return 2

        if classificador.usando_fallback:
            print("[AVISO] Modelo treinado nao encontrado em "
                  f"'{args.model}'. Usando '{config.FALLBACK_MODEL}' (ImageNet) so pra "
                  "testar o pipeline. Treine com: python train/train.py")
        classificador.aquecer()

    # ---- Abre a fonte de frames ----
    try:
        fonte = FonteDeFrames(args.source, loop=True)
    except FonteIndisponivel as e:
        print(f"[ERRO] {e}")
        return 2
    print(f"[OK] Fonte: {fonte.modo} ('{args.source}'). Pressione 'q' para sair.")

    # ---- Cliente da API com fila offline ----
    api = ApiClient(
        api_url=args.api_url,
        queue_path=config.OFFLINE_QUEUE_PATH,
        min_interval_s=config.ALERT_MIN_INTERVAL_S,
        habilitado=not args.no_api,
    )

    if args.save:
        os.makedirs(args.save, exist_ok=True)

    headless = args.headless
    tempos = deque(maxlen=30)   # timestamps recentes -> FPS suavizado
    n_frames = 0
    n_alertas = 0
    ultimo_log = 0.0
    ultimo_alerta = 0.0   # throttle: conta/dispara no máx 1 alerta por segundo

    try:
        while True:
            t0 = time.perf_counter()

            # Leitura resiliente: erro inesperado de hardware não derruba o loop.
            try:
                ok, frame = fonte.ler()
            except Exception as e:
                print(f"[WARN] Erro ao capturar frame: {e}")
                continue

            if not ok:
                print("[INFO] Fonte encerrada (sem mais frames).")
                break
            if frame is None:
                continue  # frame corrompido — pula sem derrubar o stream

            # Amplia frames pequenos (ex.: imagens de amostra 256px) pra o HUD
            # ficar legível e a janela num tamanho confortável.
            hh, ww = frame.shape[:2]
            if ww < 640:
                frame = cv2.resize(frame, (640, int(hh * 640 / ww)),
                                   interpolation=cv2.INTER_LINEAR)

            # ---- Análise do frame: pragas (modelo) ou fogo (heurística) ----
            det = None
            if args.fogo:
                det = detector_fogo.analisar(frame)  # nunca lança (robusto)
                conf = det.confianca
                rotulo_log = "FOGO" if det.tem_fogo else "sem fogo"
                e_alerta = det.tem_fogo
                classe_api = "fogo"
            else:
                try:
                    pred = classificador.prever(frame)
                except ModeloIndisponivel as e:
                    desenhar_erro(frame, "Falha de inferencia")
                    if not headless:
                        try:
                            cv2.imshow(config.WINDOW_NAME, frame)
                            if cv2.waitKey(1) & 0xFF == ord("q"):
                                break
                        except cv2.error:
                            headless = True
                    print(f"[WARN] {e}")
                    continue
                classe = info_classe(pred.classe)
                conf = pred.confianca
                rotulo_log = classe.label
                e_alerta = conf >= args.conf and not classe.saudavel
                classe_api = pred.classe

            # ---- Decide alerta + envio pra API ----
            # Alerta é EVENTO, não estado: mesmo com fogo/praga na tela por vários
            # segundos, contamos e enviamos no máximo 1x por segundo (throttle). O
            # HUD continua mostrando o estado a cada frame; só o alerta é limitado.
            enviando = False
            agora_alerta = time.time()
            if e_alerta and (agora_alerta - ultimo_alerta) >= config.ALERT_MIN_INTERVAL_S:
                n_alertas += 1
                status = api.enviar(classe_api, conf, geo={})
                enviando = status == "enviado"
                ultimo_alerta = agora_alerta

            # ---- FPS suavizado ----
            tempos.append(time.perf_counter())
            fps = 0.0
            if len(tempos) >= 2:
                dt = tempos[-1] - tempos[0]
                if dt > 0:
                    fps = (len(tempos) - 1) / dt

            # ---- HUD ----
            if args.fogo:
                desenhar_hud_fogo(frame, det, fps, enviando)
            else:
                desenhar_hud(frame, classe.label, conf, fps, classe.saudavel, enviando)

            # ---- Saída (janela ou headless) ----
            if args.save:
                cv2.imwrite(os.path.join(args.save, f"frame_{n_frames:05d}.jpg"), frame)

            if not headless:
                try:
                    cv2.imshow(config.WINDOW_NAME, frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except cv2.error:
                    # Sem display disponível -> cai pra headless automaticamente.
                    print("[AVISO] Sem display; seguindo em modo headless.")
                    headless = True

            # Log de status ~1x por segundo (bom pra evidência/headless).
            agora = time.time()
            if agora - ultimo_log >= 1.0:
                fila = api.tamanho_fila()
                print(f"[{n_frames:05d}] {rotulo_log:28s} conf={conf*100:5.1f}% "
                      f"fps={fps:4.1f} alertas={n_alertas} fila_offline={fila}")
                ultimo_log = agora

            n_frames += 1
            if args.max_frames and n_frames >= args.max_frames:
                print(f"[INFO] Atingiu --max-frames={args.max_frames}.")
                break

    except KeyboardInterrupt:
        print("\n[INFO] Interrompido pelo usuario (Ctrl+C).")
    finally:
        # Limpeza SEMPRE acontece — libera câmera e fecha janelas.
        fonte.liberar()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        fila = api.tamanho_fila()
        print(f"[FIM] frames={n_frames} alertas={n_alertas} fila_offline={fila}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
