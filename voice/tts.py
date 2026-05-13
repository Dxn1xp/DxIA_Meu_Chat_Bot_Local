"""
voice/tts.py — v2.0  E2
Motor TTS com suporte a:
  1. Kokoro-82M (local, neural, alta qualidade, offline)
  2. edge-tts (Microsoft Neural, requer internet)
  3. pyttsx3 (fallback offline sempre disponível)

Instalação Kokoro:
  pip install kokoro soundfile numpy
  # Modelo baixado automaticamente (~82MB) na primeira execução

Instalação edge-tts:
  pip install edge-tts

Vozes Kokoro disponíveis:
  af_bella, af_sarah, am_adam, am_michael
  bf_emma, bf_isabella, bm_george, bm_lewis
"""

import asyncio
import io
import threading
import queue
import time
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)

TTS_CFG  = config.get("tts", {})
ENGINE   = TTS_CFG.get("engine", "kokoro")
VOZ      = TTS_CFG.get("voz", "bf_emma")
VEL      = float(TTS_CFG.get("velocidade", 1.1))
MAX_FALA = int(TTS_CFG.get("max_chars_falar", 400))
RESUMIR  = TTS_CFG.get("resumir_longas", True)


class TTSEngine:
    """Motor de síntese de voz com fallback automático em cascata."""

    def __init__(self):
        self._engine_nome = ENGINE
        self._kokoro      = None
        self._pyttsx3     = None
        self.available    = False
        self._fila: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._ativo = False

    def load(self) -> bool:
        """Tenta carregar engines na ordem de preferência."""
        if ENGINE == "kokoro" or ENGINE == "auto":
            if self._load_kokoro():
                self._engine_nome = "kokoro"
                self.available = True
                self._iniciar_worker()
                logger.info("TTS: Kokoro-82M carregado.")
                return True

        if ENGINE in ("edge", "auto"):
            # edge-tts é async — verificação simples
            try:
                import edge_tts
                self._engine_nome = "edge"
                self.available = True
                self._iniciar_worker()
                logger.info("TTS: edge-tts carregado.")
                return True
            except ImportError:
                logger.warning("edge-tts não instalado. pip install edge-tts")

        if self._load_pyttsx3():
            self._engine_nome = "pyttsx3"
            self.available = True
            self._iniciar_worker()
            logger.info("TTS: pyttsx3 carregado (fallback).")
            return True

        logger.warning("Nenhum motor TTS disponível.")
        return False

    def falar(self, texto: str, bloquear: bool = False) -> None:
        """Enfileira texto para fala. Thread-safe."""
        if not self.available or not texto.strip():
            return

        # Resumir se texto muito longo
        if RESUMIR and len(texto) > MAX_FALA:
            texto = self._resumir(texto)

        if bloquear:
            self._falar_sync(texto)
        else:
            self._fila.put(texto)

    def parar(self) -> None:
        """Para a fala atual e encerra o worker."""
        self._ativo = False
        # Drena a fila
        while not self._fila.empty():
            try: self._fila.get_nowait()
            except: break

    def listar_vozes_kokoro(self) -> list[str]:
        return [
            "af_bella", "af_sarah", "af_sky", "af_nicole",
            "am_adam", "am_michael",
            "bf_emma", "bf_isabella",
            "bm_george", "bm_lewis",
        ]

    # ── Worker thread ─────────────────────────────────────────────

    def _iniciar_worker(self):
        self._ativo = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self):
        while self._ativo:
            try:
                texto = self._fila.get(timeout=0.5)
                self._falar_sync(texto)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS worker: {e}")

    def _falar_sync(self, texto: str):
        """Fala de forma síncrona usando o engine disponível."""
        try:
            if self._engine_nome == "kokoro":
                self._falar_kokoro(texto)
            elif self._engine_nome == "edge":
                asyncio.run(self._falar_edge(texto))
            else:
                self._falar_pyttsx3(texto)
        except Exception as e:
            logger.error(f"TTS falar: {e}")
            # Fallback: tenta pyttsx3
            if self._engine_nome != "pyttsx3":
                self._falar_pyttsx3(texto)

    # ── Kokoro ────────────────────────────────────────────────────

    def _load_kokoro(self) -> bool:
        try:
            from kokoro import KPipeline
            # Pipeline PT ou EN dependendo da voz
            lang = "b" if VOZ.startswith("b") else "a"
            self._kokoro = KPipeline(lang_code=lang)
            return True
        except ImportError:
            logger.warning("Kokoro não instalado. pip install kokoro soundfile numpy")
            return False
        except Exception as e:
            logger.warning(f"Kokoro load: {e}")
            return False

    def _falar_kokoro(self, texto: str):
        """Gera áudio com Kokoro e reproduz via sounddevice."""
        try:
            import sounddevice as sd
            import numpy as np

            generator = self._kokoro(texto, voice=VOZ, speed=VEL)
            for _, _, audio in generator:
                if audio is not None and len(audio) > 0:
                    # Kokoro retorna float32 @ 24000 Hz
                    sd.play(audio, samplerate=24000)
                    sd.wait()
        except Exception as e:
            logger.error(f"Kokoro falar: {e}")
            raise

    # ── edge-tts ──────────────────────────────────────────────────

    async def _falar_edge(self, texto: str):
        """Síntese via Microsoft Edge Neural TTS (requer internet)."""
        try:
            import edge_tts
            import soundfile as sf
            import sounddevice as sd
            import tempfile, os

            # Voz PT-BR padrão se não for voz Kokoro
            voz_edge = "pt-BR-FranciscaNeural"

            tts = edge_tts.Communicate(texto, voice=voz_edge,
                                        rate=f"+{int((VEL-1)*100)}%")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp = f.name

            await tts.save(tmp)
            data, sr = sf.read(tmp)
            sd.play(data, samplerate=sr)
            sd.wait()
            os.unlink(tmp)
        except Exception as e:
            logger.error(f"edge-tts: {e}")
            raise

    # ── pyttsx3 ───────────────────────────────────────────────────

    def _load_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            self._pyttsx3 = pyttsx3.init()
            self._pyttsx3.setProperty("rate", int(175 * VEL))
            self._pyttsx3.setProperty("volume", 0.9)
            # Selecionar voz PT-BR
            for v in self._pyttsx3.getProperty("voices"):
                if "maria" in v.name.lower() or "francisca" in v.name.lower():
                    self._pyttsx3.setProperty("voice", v.id)
                    break
            return True
        except ImportError:
            return False
        except Exception as e:
            logger.warning(f"pyttsx3: {e}")
            return False

    def _falar_pyttsx3(self, texto: str):
        if self._pyttsx3:
            try:
                self._pyttsx3.say(texto)
                self._pyttsx3.runAndWait()
            except Exception as e:
                logger.error(f"pyttsx3 falar: {e}")

    # ── Utilitários ───────────────────────────────────────────────

    def _resumir(self, texto: str) -> str:
        """
        Resumo simples: pega as primeiras frases até o limite.
        Na Fase 3 isso vai usar a IA para resumir.
        """
        frases = texto.replace("!\n", ". ").replace("?\n", ". ").split(". ")
        resultado = []
        total = 0
        for f in frases:
            if total + len(f) > MAX_FALA:
                break
            resultado.append(f)
            total += len(f)
        return ". ".join(resultado) + ("..." if len(frases) > len(resultado) else "")
