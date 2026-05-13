"""
system/monitor.py — v2.1
Monitor de RAM/CPU com dashboard no terminal.
"""

import time, threading, os, psutil
from utils.logger import get_logger

logger = get_logger(__name__)

_G = "\033[92m"; _R = "\033[91m"; _A = "\033[93m"; _X = "\033[0m"; _B = "\033[1m"
RAM_LIMITE_MB = 2048
CPU_LIMITE    = 85
INTERVALO     = 15


class ResourceMonitor:

    def __init__(self):
        self._ativo    = False
        self._thread   = None
        self._historico: list[dict] = []
        self._pid      = os.getpid()

    def iniciar(self):
        self._ativo  = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def parar(self):
        self._ativo = False

    def snapshot(self) -> dict:
        proc = psutil.Process(self._pid)
        ram  = proc.memory_info().rss / 1024 / 1024
        cpu  = psutil.cpu_percent(interval=0.3)
        mem  = psutil.virtual_memory()
        return {
            "ram_assistente_mb": round(ram, 1),
            "ram_sistema_pct":   round(mem.percent, 1),
            "ram_livre_mb":      round(mem.available / 1024 / 1024),
            "cpu_pct":           round(cpu, 1),
            "dentro_do_limite":  ram < RAM_LIMITE_MB,
        }

    def relatorio(self) -> str:
        s = self.snapshot()
        cor_ram = _G if s["dentro_do_limite"] else _R
        cor_cpu = _G if s["cpu_pct"] < CPU_LIMITE else _A
        return (
            f"{_B}Monitor de recursos{_X}\n"
            f"  RAM assistente: {cor_ram}{s['ram_assistente_mb']} MB{_X} / {RAM_LIMITE_MB} MB\n"
            f"  RAM sistema:    {s['ram_sistema_pct']}% | {s['ram_livre_mb']} MB livres\n"
            f"  CPU:            {cor_cpu}{s['cpu_pct']}%{_X}"
        )

    def media(self) -> dict:
        if not self._historico: return {}
        n = len(self._historico)
        return {
            "ram_media": round(sum(h["ram_assistente_mb"] for h in self._historico)/n, 1),
            "cpu_media": round(sum(h["cpu_pct"] for h in self._historico)/n, 1),
        }

    def _loop(self):
        while self._ativo:
            try:
                s = self.snapshot()
                self._historico.append(s)
                if len(self._historico) > 60:
                    self._historico.pop(0)
                if not s["dentro_do_limite"]:
                    logger.warning(f"RAM alta: {s['ram_assistente_mb']:.0f} MB")
            except Exception as e:
                logger.debug(f"Monitor: {e}")
            time.sleep(INTERVALO)
