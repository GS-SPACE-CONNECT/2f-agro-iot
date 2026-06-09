"""
Cliente da API de alertas (backend C# .NET) com fila offline.

Quando o "Olho na Folha" detecta uma praga com confiança suficiente, manda um
POST pra API. Requisitos de robustez (rubrica):
  * o stream de vídeo NUNCA pode cair por causa de rede — toda falha é capturada;
  * se a API estiver fora do ar, o diagnóstico é gravado numa fila local (JSONL)
    e reenviado automaticamente quando a API voltar;
  * throttle por praga, pra não floodar a API com o mesmo alerta a 30 fps.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

try:
    import requests
    _TEM_REQUESTS = True
except ImportError:  # degrada com elegância — sem requests, tudo vai pra fila
    requests = None  # type: ignore
    _TEM_REQUESTS = False


class ApiClient:
    """Envia diagnósticos pra API, com throttle e fila offline persistente."""

    def __init__(self, api_url: str, queue_path: str,
                 min_interval_s: float = 5.0, timeout: float = 2.0,
                 habilitado: bool = True) -> None:
        self.api_url = api_url
        self.queue_path = queue_path
        self.min_interval_s = min_interval_s
        self.timeout = timeout
        self.habilitado = habilitado and _TEM_REQUESTS
        self._ultimo_envio: dict[str, float] = {}

    # ----------------------------------------------------------------- #
    # API pública
    # ----------------------------------------------------------------- #
    def enviar(self, praga: str, confianca: float,
               geo: Optional[dict] = None) -> str:
        """
        Tenta enviar um diagnóstico. Retorna um status legível:
            'enviado'    — POST aceito pela API
            'enfileirado'— API indisponível, salvo na fila offline
            'throttled'  — mesma praga enviada há pouco (ignorado de propósito)
            'desligado'  — cliente desabilitado (--no-api ou sem requests)
        Nunca lança exceção: erro de rede é tratado internamente.
        """
        agora = time.time()
        ultimo = self._ultimo_envio.get(praga, 0.0)
        if agora - ultimo < self.min_interval_s:
            return "throttled"
        self._ultimo_envio[praga] = agora

        payload = {
            "praga": praga,
            "confianca": round(float(confianca), 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "geo": geo or {},
        }

        if not self.habilitado:
            # Mesmo desligado, registramos na fila pra histórico/integração.
            self._enfileirar(payload)
            return "desligado"

        try:
            resp = requests.post(self.api_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            # Deu certo: aproveita pra drenar o que ficou preso offline.
            self.flush()
            return "enviado"
        except Exception:  # ConnectionError, Timeout, HTTPError, etc.
            # NUNCA propaga: salva offline e segue a vida.
            self._enfileirar(payload)
            return "enfileirado"

    def flush(self) -> int:
        """
        Reenvia os diagnósticos presos na fila offline. Mantém na fila os que
        ainda falharem. Retorna quantos foram enviados com sucesso.
        """
        if not self.habilitado or not os.path.exists(self.queue_path):
            return 0

        try:
            with open(self.queue_path, "r", encoding="utf-8") as fh:
                linhas = [ln for ln in fh.read().splitlines() if ln.strip()]
        except OSError:
            return 0

        if not linhas:
            return 0

        pendentes: list[str] = []
        enviados = 0
        for ln in linhas:
            try:
                payload = json.loads(ln)
            except json.JSONDecodeError:
                continue  # descarta linha corrompida
            try:
                resp = requests.post(self.api_url, json=payload,
                                     timeout=self.timeout)
                resp.raise_for_status()
                enviados += 1
            except Exception:
                pendentes.append(ln)

        # Reescreve a fila só com o que continua pendente.
        try:
            with open(self.queue_path, "w", encoding="utf-8") as fh:
                if pendentes:
                    fh.write("\n".join(pendentes) + "\n")
        except OSError:
            pass
        return enviados

    def tamanho_fila(self) -> int:
        """Quantos diagnósticos estão aguardando na fila offline."""
        if not os.path.exists(self.queue_path):
            return 0
        try:
            with open(self.queue_path, "r", encoding="utf-8") as fh:
                return sum(1 for ln in fh if ln.strip())
        except OSError:
            return 0

    # ----------------------------------------------------------------- #
    # Interno
    # ----------------------------------------------------------------- #
    def _enfileirar(self, payload: dict) -> None:
        """Acrescenta um diagnóstico na fila offline (append JSONL)."""
        try:
            with open(self.queue_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            # Se nem o disco aceitar, não há o que fazer — mas não derrubamos
            # o stream por isso.
            pass
