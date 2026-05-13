"""
voice/voice_loop.py — v2.1  E6-01
Loop de voz em processo independente usando multiprocessing.
Não bloqueia o pipeline principal de texto/IA.

Arquitetura:
  MainProcess  ←── Queue ──  VoiceProcess
  (IA/comandos)              (STT contínuo)

O processo de voz escuta o microfone e coloca texto na fila.
O processo principal consome a fila e processa os textos.
"""

import multiprocessing as mp
import queue
import threading
import time
from utils.logger import get_logger

logger = get_logger(__name__)

_G = "\033[92m"; _R = "\033[91m"; _A = "\033[93m"; _X = "\033[0m"


def _worker_voz(fila_out: mp.Queue, parar: mp.Event,
                modelo_path: str, silencio: float):
    """
    Roda em processo separado.
    Ouve microfone continuamente e envia texto para fila_out.
    """
    import json, queue as q_thread
    from pathlib import Path

    try:
        from vosk import Model, KaldiRecognizer
        import sounddevice as sd
    except ImportError:
        fila_out.put({"tipo": "erro", "msg": "vosk/sounddevice não instalado"})
        return

    if not Path(modelo_path).exists():
        fila_out.put({"tipo": "erro", "msg": f"Modelo não encontrado: {modelo_path}"})
        return

    model = Model(modelo_path)
    rec   = KaldiRecognizer(model, 16000)

    audio_q: q_thread.Queue = q_thread.Queue()

    def cb(indata, frames, t, status):
        audio_q.put(bytes(indata))

    fila_out.put({"tipo": "pronto"})

    ultimo = time.time()
    acum   = []

    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                            dtype="int16", channels=1, callback=cb):
        while not parar.is_set():
            try:
                data = audio_q.get(timeout=0.3)
                ultimo = time.time()
                acum.append(data)
                if rec.AcceptWaveform(data):
                    texto = json.loads(rec.Result()).get("text", "").strip()
                    if texto:
                        fila_out.put({"tipo": "texto", "texto": texto})
                    acum = []
            except q_thread.Empty:
                if acum and (time.time() - ultimo) > silencio:
                    texto = json.loads(rec.FinalResult()).get("text", "").strip()
                    if texto:
                        fila_out.put({"tipo": "texto", "texto": texto})
                    acum = []
                    ultimo = time.time()


class VoiceLoop:
    """
    Gerencia o processo de voz e expõe uma interface simples.
    O callback é chamado na thread principal com o texto transcrito.
    """

    def __init__(self, modelo_path: str = "models/vosk-model-pt",
                 silencio: float = 1.5):
        self._modelo  = modelo_path
        self._silencio= silencio
        self._processo: mp.Process | None = None
        self._fila    = mp.Queue()
        self._parar   = mp.Event()
        self._callback = None
        self._consumer: threading.Thread | None = None
        self.ativo    = False

    def iniciar(self, callback) -> bool:
        """
        Inicia o processo de voz e começa a consumir resultados.
        callback(texto: str) é chamado para cada frase detectada.
        """
        self._callback = callback
        self._parar.clear()

        self._processo = mp.Process(
            target=_worker_voz,
            args=(self._fila, self._parar, self._modelo, self._silencio),
            daemon=True,
        )
        self._processo.start()

        # Aguarda o processo confirmar que está pronto
        try:
            msg = self._fila.get(timeout=10.0)
            if msg.get("tipo") == "erro":
                logger.error(f"VoiceLoop: {msg.get('msg')}")
                return False
        except Exception:
            logger.error("VoiceLoop: timeout aguardando processo de voz.")
            return False

        self.ativo = True
        self._consumer = threading.Thread(target=self._consumir, daemon=True)
        self._consumer.start()
        print(f"\n  {_G}[VOZ CONTÍNUA ATIVA]{_X}  Ctrl+Alt+M para pausar.\n")
        return True

    def parar(self):
        self._parar.set()
        self.ativo = False
        if self._processo and self._processo.is_alive():
            self._processo.terminate()
            self._processo.join(timeout=3)
        print(f"\n  {_R}[VOZ DESATIVADA]{_X}\n")

    def _consumir(self):
        """Thread que lê a fila e chama o callback."""
        while self.ativo:
            try:
                msg = self._fila.get(timeout=0.5)
                if msg.get("tipo") == "texto" and self._callback:
                    self._callback(msg["texto"])
            except Exception:
                continue
