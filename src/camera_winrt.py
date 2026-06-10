"""
Backend alternativo de webcam via WinRT (Windows.Media.Capture).

Por que existe: em alguns Windows o caminho clássico de captura que o OpenCV usa
(Media Foundation "legado" e DirectShow) fica quebrado — tipicamente por resíduo
de driver/software antigo do fabricante — e o `cv2.VideoCapture(0)` falha com
"Failed to activate media source" mesmo com a câmera OK no sistema. O caminho
moderno (WinRT, o mesmo do app Câmera do Windows) continua funcionando, então
este módulo abre a câmera por ele e entrega frames BGR prontos pro OpenCV.

A classe `CameraWinRT` imita a interface do `cv2.VideoCapture` (`read()`,
`release()`, `isOpened()`), então o `FonteDeFrames` usa uma ou outra sem o
restante do pipeline perceber a diferença.

Dependências (só Windows): pacotes `winrt-*` listados no requirements.txt com
marker `sys_platform == "win32"`.
"""
from __future__ import annotations

import asyncio
import threading

import numpy as np

from winrt.windows.graphics.imaging import (
    BitmapBufferAccessMode,
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winrt.windows.media.capture import (
    MediaCapture,
    MediaCaptureInitializationSettings,
    MediaCaptureMemoryPreference,
    MediaCaptureSharingMode,
    MediaStreamType,
    StreamingCaptureMode,
)
from winrt.windows.media.capture.frames import (
    MediaFrameReaderAcquisitionMode,
    MediaFrameReaderStartStatus,
    MediaFrameSourceGroup,
    MediaFrameSourceKind,
)


class CameraWinRTIndisponivel(RuntimeError):
    """Nem o WinRT conseguiu abrir a câmera pedida."""


class CameraWinRT:
    """Webcam via WinRT com a mesma interface de leitura do cv2.VideoCapture."""

    def __init__(self, indice: int = 0, timeout_s: float = 15.0):
        self._aberta = False
        self._mc = None
        self._reader = None
        # WinRT é assíncrono; rodamos um event loop num thread dedicado e
        # criamos/usamos os objetos sempre nele (evita briga de apartamento COM).
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="camera-winrt", daemon=True
        )
        self._thread.start()
        try:
            fut = asyncio.run_coroutine_threadsafe(self._abrir(indice), self._loop)
            fut.result(timeout_s)
            self._aberta = True
        except Exception as e:
            self.release()
            raise CameraWinRTIndisponivel(
                f"WinRT nao abriu a camera {indice}: {e}"
            ) from e

    # ------------------------------------------------------------------ #
    async def _abrir(self, indice: int) -> None:
        grupos = await MediaFrameSourceGroup.find_all_async()
        # Só grupos que têm fonte de vídeo colorida (ignora IR/depth/virtuais).
        candidatos = []
        for g in grupos:
            for info in g.source_infos:
                if info.source_kind == MediaFrameSourceKind.COLOR and \
                   info.media_stream_type in (MediaStreamType.VIDEO_RECORD,
                                              MediaStreamType.VIDEO_PREVIEW):
                    candidatos.append(g)
                    break
        if indice >= len(candidatos):
            raise CameraWinRTIndisponivel(
                f"indice {indice} fora do alcance ({len(candidatos)} camera(s) WinRT)"
            )

        settings = MediaCaptureInitializationSettings()
        settings.source_group = candidatos[indice]
        settings.streaming_capture_mode = StreamingCaptureMode.VIDEO
        settings.memory_preference = MediaCaptureMemoryPreference.CPU
        settings.sharing_mode = MediaCaptureSharingMode.EXCLUSIVE_CONTROL

        self._mc = MediaCapture()
        # pywinrt expõe o overload com settings sob nome próprio.
        await self._mc.initialize_with_settings_async(settings)

        fonte = None
        for chave in self._mc.frame_sources:
            s = self._mc.frame_sources[chave]
            if s.info.source_kind == MediaFrameSourceKind.COLOR:
                fonte = s
                break
        if fonte is None:
            raise CameraWinRTIndisponivel("camera sem fonte de video colorida")

        self._reader = await self._mc.create_frame_reader_async(fonte)
        self._reader.acquisition_mode = MediaFrameReaderAcquisitionMode.REALTIME
        status = await self._reader.start_async()
        if status != MediaFrameReaderStartStatus.SUCCESS:
            raise CameraWinRTIndisponivel(f"frame reader nao iniciou: {status}")

    # ------------------------------------------------------------------ #
    async def _ler(self, espera_max_s: float = 2.0):
        """Pega o frame mais recente; espera um pouco se ainda não chegou."""
        passos = max(1, int(espera_max_s / 0.01))
        for _ in range(passos):
            ref = self._reader.try_acquire_latest_frame()
            if ref is not None:
                try:
                    vmf = ref.video_media_frame
                    sb = vmf.software_bitmap if vmf else None
                    if sb is not None:
                        return True, self._para_bgr(sb)
                finally:
                    ref.close()
            await asyncio.sleep(0.01)
        return False, None

    @staticmethod
    def _para_bgr(sb: SoftwareBitmap) -> np.ndarray:
        if sb.bitmap_pixel_format != BitmapPixelFormat.BGRA8:
            sb = SoftwareBitmap.convert(sb, BitmapPixelFormat.BGRA8)
        bb = sb.lock_buffer(BitmapBufferAccessMode.READ)
        try:
            ref = bb.create_reference()
            try:
                bruto = np.frombuffer(memoryview(ref), dtype=np.uint8)
                d = bb.get_plane_description(0)
                linhas = bruto[d.start_index:d.start_index + d.stride * d.height]
                bgra = linhas.reshape(d.height, d.stride)[:, :d.width * 4]
                bgra = bgra.reshape(d.height, d.width, 4)
                return bgra[:, :, :3].copy()  # BGR contíguo, independente do buffer
            finally:
                ref.close()
        finally:
            bb.close()

    # ------------------- interface compatível com cv2 ------------------ #
    def read(self):
        if not self._aberta:
            return False, None
        try:
            fut = asyncio.run_coroutine_threadsafe(self._ler(), self._loop)
            return fut.result(5.0)
        except Exception:
            return False, None

    def isOpened(self) -> bool:  # noqa: N802 — espelha a API do cv2
        return self._aberta

    def release(self) -> None:
        self._aberta = False
        if self._loop.is_running():
            try:
                fut = asyncio.run_coroutine_threadsafe(self._fechar(), self._loop)
                fut.result(5.0)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2.0)

    async def _fechar(self) -> None:
        if self._reader is not None:
            try:
                await self._reader.stop_async()
            except Exception:
                pass
            self._reader = None
        if self._mc is not None:
            try:
                self._mc.close()
            except Exception:
                pass
            self._mc = None
