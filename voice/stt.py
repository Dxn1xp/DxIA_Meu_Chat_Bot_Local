"""
voice/stt.py — v2.0  E3
Modo contínuo de escuta com:
  - Detecção de silêncio automática (VAD)
  - Hotkey global para toggle (Ctrl+Alt+M)
  - Indicador visual no terminal
  - Comandos "ativar escuta" / "desativar escuta"
  - Push-to-talk opcional
"""

import json
import queue
import threading
import time
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)

STT_CFG  = config.get("stt", {})
MODEL_PATH    = STT_CFG.get("modelo_path", "models/vosk-model-pt")
SILENCIO_SEC  = float(STT_CFG.get("silencio_timeout", 1.5))
HOTKEY        = STT_CFG.get("hotkey_toggle", "<ctrl>+<alt>+m")
SAMPLE_RATE   = 16000
BLOCK_SIZE    = 8000

# Cores ANSI para terminal
_VERDE   = "\033[92m"
_VERMELHO = "\033[91m"
_RESET   = "\033[0m"
_AMARELO = "\033[93m"


class STTEngine:
    """Transcrição de voz com modo contínuo e toggle de microfone."""

    def __init__(self):
        self._model       = None
        self._recognizer  = None
        self.available    = False
        self._escutando   = False
        self._callback    = None      # chamado com texto transcrito
        self._thread: threading.Thread | None = None
        self._hotkey_thread: threading.Thread | None = None
        self._parar_flag  = threading.Event()

    def load(self) -> bool:
        """Carrega modelo Vosk."""
        try:
            from vosk import Model, KaldiRecognizer
            from pathlib import Path
            p = Path(MODEL_PATH)
            if not p.exists():
                logger.warning(
                    f"Modelo Vosk não encontrado em '{MODEL_PATH}'.\n"
                    f"  Baixe: https://alphacephei.com/vosk/models\n"
                    f"  Extraia para: {MODEL_PATH}"
                )
                return False
            self._model      = Model(str(p))
            self._recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
            self.available   = True
            logger.info("STT (Vosk) carregado.")
            return True
        except ImportError:
            logger.warning("Vosk não instalado. pip install vosk sounddevice")
            return False
        except Exception as e:
            logger.error(f"STT load: {e}")
            return False

    # ── API pública ───────────────────────────────────────────────

    def ouvir(self, timeout: float = 6.0) -> str | None:
        """Ouve UMA frase e retorna o texto. Modo one-shot."""
        if not self.available:
            return None
        return self._capturar(timeout=timeout)

    def iniciar_modo_continuo(self, callback) -> None:
        """
        Inicia loop contínuo de escuta.
        callback(texto: str) é chamado a cada frase detectada.
        """
        if not self.available:
            logger.warning("STT indisponível.")
            return
        self._callback    = callback
        self._parar_flag.clear()
        self._escutando   = True
        self._thread = threading.Thread(target=self._loop_continuo, daemon=True)
        self._thread.start()
        self._iniciar_hotkey()
        self._mostrar_status()
        logger.info(f"Modo contínuo ativo. Toggle: {HOTKEY}")

    def parar_modo_continuo(self) -> None:
        """Para o loop de escuta."""
        self._escutando = False
        self._parar_flag.set()
        self._mostrar_status()
        logger.info("Modo contínuo desativado.")

    def toggle_escuta(self) -> bool:
        """Alterna entre ouvir e silencioso. Retorna novo estado."""
        if self._escutando:
            self._escutando = False
        else:
            self._escutando = True
            self._parar_flag.clear()
        self._mostrar_status()
        return self._escutando

    @property
    def esta_escutando(self) -> bool:
        return self._escutando

    # ── Loop contínuo ─────────────────────────────────────────────

    def _loop_continuo(self):
        """Loop de captura contínua com detecção de silêncio (VAD)."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.warning("sounddevice não instalado.")
            return

        audio_q: queue.Queue = queue.Queue()

        def callback_sd(indata, frames, time_info, status):
            if self._escutando:
                audio_q.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
            dtype="int16", channels=1, callback=callback_sd,
        ):
            ultimo_audio = time.time()
            acumulado   = []

            while not self._parar_flag.is_set():
                if not self._escutando:
                    time.sleep(0.1)
                    ultimo_audio = time.time()
                    acumulado   = []
                    continue

                try:
                    data = audio_q.get(timeout=0.3)
                    ultimo_audio = time.time()
                    acumulado.append(data)

                    if self._recognizer.AcceptWaveform(data):
                        res = json.loads(self._recognizer.Result())
                        texto = res.get("text", "").strip()
                        if texto and self._callback:
                            self._callback(texto)
                        acumulado = []

                except queue.Empty:
                    # Silêncio por SILENCIO_SEC → processa parcial
                    if acumulado and (time.time() - ultimo_audio) > SILENCIO_SEC:
                        res = json.loads(self._recognizer.FinalResult())
                        texto = res.get("text", "").strip()
                        if texto and self._callback:
                            self._callback(texto)
                        acumulado = []
                        ultimo_audio = time.time()

    # ── Captura one-shot ──────────────────────────────────────────

    def _capturar(self, timeout: float) -> str | None:
        try:
            import sounddevice as sd
        except ImportError:
            return None

        audio_q: queue.Queue = queue.Queue()

        def cb(indata, frames, t, status):
            audio_q.put(bytes(indata))

        resultado = []
        with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                                dtype="int16", channels=1, callback=cb):
            fim = time.time() + timeout
            while time.time() < fim:
                try:
                    data = audio_q.get(timeout=0.5)
                    if self._recognizer.AcceptWaveform(data):
                        t = json.loads(self._recognizer.Result()).get("text", "")
                        if t:
                            resultado.append(t)
                            break
                except queue.Empty:
                    pass

            if not resultado:
                t = json.loads(self._recognizer.FinalResult()).get("text", "")
                if t:
                    resultado.append(t)

        texto = " ".join(resultado).strip()
        return texto if texto else None

    # ── Hotkey global ─────────────────────────────────────────────

    def _iniciar_hotkey(self):
        def _loop():
            try:
                from pynput import keyboard
                with keyboard.GlobalHotKeys({HOTKEY: self.toggle_escuta}) as hk:
                    hk.join()
            except ImportError:
                logger.warning("pynput não instalado. Hotkey desativado.")
            except Exception as e:
                logger.debug(f"Hotkey: {e}")

        self._hotkey_thread = threading.Thread(target=_loop, daemon=True)
        self._hotkey_thread.start()

    # ── Status visual ─────────────────────────────────────────────

    def _mostrar_status(self):
        if self._escutando:
            print(f"\n  {_VERDE}[OUVINDO]{_RESET}  Microfone ativo — fale a qualquer momento.")
            print(f"  Toggle: {HOTKEY} | Comando: 'desativar escuta'\n")
        else:
            print(f"\n  {_VERMELHO}[MUDO]{_RESET}  Microfone desativado.")
            print(f"  Toggle: {HOTKEY} | Comando: 'ativar escuta'\n")
