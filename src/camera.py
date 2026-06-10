"""
Fonte de frames resiliente.

Abstrai DE ONDE vêm os frames pra que o `olho_na_folha.py` seja idêntico tanto na
demo ao vivo quanto nos testes headless:

    --source 0            -> webcam (índice 0) — modo demo
    --source video.mp4    -> arquivo de vídeo
    --source pasta/       -> pasta de imagens (cicla) — ótimo pra testar sem webcam
    --source folha.jpg    -> uma imagem só (repetida)

Robustez (rubrica): se a webcam cair no meio do stream, tenta reconectar algumas
vezes antes de desistir, em vez de derrubar o programa.
"""
from __future__ import annotations

import os
import cv2

IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
VIDEO_EXTS = (".mp4", ".avi", ".mov", ".mkv", ".webm")


class FonteIndisponivel(RuntimeError):
    """Erro claro quando a fonte (webcam/arquivo) não pôde ser aberta."""


class FonteDeFrames:
    """Itera frames de webcam, vídeo, pasta de imagens ou imagem única."""

    def __init__(self, source, loop: bool = True, max_reconexoes: int = 5):
        self.source = source
        self.loop = loop
        self.max_reconexoes = max_reconexoes
        self._cap = None
        self._imgs: list[str] = []
        self._idx = 0
        self.modo = self._detectar_modo(source)
        self._abrir()

    # ----------------------------------------------------------------- #
    def _detectar_modo(self, source) -> str:
        if isinstance(source, int) or (isinstance(source, str) and source.isdigit()):
            return "camera"
        if isinstance(source, str):
            if os.path.isdir(source):
                return "imagens"
            if os.path.isfile(source):
                ext = os.path.splitext(source)[1].lower()
                if ext in IMG_EXTS:
                    return "imagem"
                if ext in VIDEO_EXTS:
                    return "video"
                return "video"  # tenta como stream/container desconhecido
        return "video"  # ex.: URL RTSP

    def _abrir(self) -> None:
        if self.modo == "camera":
            indice = int(self.source)
            self._cap = self._abrir_camera(indice)
            if self._cap is None:
                raise FonteIndisponivel(
                    f"Webcam no indice {indice} indisponivel. Conecte uma camera "
                    f"ou use --source <pasta_de_imagens> para testar sem webcam."
                )
        elif self.modo in ("video",):
            self._cap = cv2.VideoCapture(self.source)
            if not self._cap or not self._cap.isOpened():
                raise FonteIndisponivel(f"Nao consegui abrir o video: {self.source}")
        elif self.modo == "imagens":
            self._imgs = sorted(
                os.path.join(self.source, f)
                for f in os.listdir(self.source)
                if f.lower().endswith(IMG_EXTS)
            )
            if not self._imgs:
                raise FonteIndisponivel(f"Nenhuma imagem em: {self.source}")
        elif self.modo == "imagem":
            self._imgs = [self.source]

    def _abrir_camera(self, indice: int):
        """Abre a webcam: OpenCV primeiro; se falhar, fallback WinRT (Windows).

        Em alguns Windows o backend clássico do OpenCV (MSMF/DSHOW) quebra por
        resíduo de driver antigo, mas o caminho WinRT — o mesmo do app Câmera —
        segue funcionando. Retorna um objeto com a interface do VideoCapture
        (read/release/isOpened) ou None se nada abriu.
        """
        cap = cv2.VideoCapture(indice)
        if cap is not None and cap.isOpened():
            return cap
        try:
            cap.release()
        except Exception:
            pass
        try:
            from src.camera_winrt import CameraWinRT, CameraWinRTIndisponivel
        except ImportError:
            return None  # fora do Windows (ou sem winrt-*) não há fallback
        try:
            camera = CameraWinRT(indice)
        except CameraWinRTIndisponivel as e:
            print(f"[WARN] Fallback WinRT tambem falhou: {e}")
            return None
        print("[INFO] OpenCV nao abriu a webcam; usando backend WinRT do Windows.")
        return camera

    # ----------------------------------------------------------------- #
    def ler(self):
        """Retorna (ok: bool, frame|None). Trata reconexão de webcam/vídeo."""
        if self.modo in ("imagens", "imagem"):
            return self._ler_imagem()
        return self._ler_captura()

    def _ler_imagem(self):
        if self._idx >= len(self._imgs):
            if not self.loop:
                return False, None
            self._idx = 0
        caminho = self._imgs[self._idx]
        self._idx += 1
        frame = cv2.imread(caminho)
        if frame is None:  # arquivo corrompido — pula sem quebrar
            return True, None
        return True, frame

    def _ler_captura(self):
        # Protege o .read() contra exceções de hardware (ex.: webcam desconectada
        # no meio do stream). Sem esse try/except, uma falha de I/O no driver
        # mataria o programa em vez de acionar a reconexão.
        try:
            ok, frame = self._cap.read()
        except Exception:
            ok, frame = False, None
        if ok and frame is not None:
            return True, frame

        # Fim de vídeo: reinicia se loop ligado.
        if self.modo == "video" and self.loop:
            try:
                self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            except Exception:
                ok, frame = False, None
            if ok and frame is not None:
                return True, frame

        # Webcam que travou: tenta reconectar N vezes antes de desistir.
        if self.modo == "camera":
            for tentativa in range(1, self.max_reconexoes + 1):
                print(f"[WARN] Webcam falhou — reconexao "
                      f"{tentativa}/{self.max_reconexoes}")
                try:
                    self._cap.release()
                except Exception:
                    pass
                try:
                    self._cap = self._abrir_camera(int(self.source))
                    if self._cap is None:
                        continue
                    ok, frame = self._cap.read()
                except Exception:
                    ok, frame = False, None
                if ok and frame is not None:
                    print("[OK] Webcam reconectada.")
                    return True, frame
            return False, None

        return False, None  # vídeo sem loop chegou ao fim

    def liberar(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
