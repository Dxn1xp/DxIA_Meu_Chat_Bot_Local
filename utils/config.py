from pathlib import Path
import yaml

_CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"
_DEFAULTS = {
    "ollama_url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "inference": {"num_ctx":4096,"num_predict":768,"temperature":0.75,
                  "repeat_penalty":1.1,"num_thread":10,"top_p":0.9},
    "cache": {"enabled":True,"ttl_minutos":60,"max_entradas":200},
    "usuario": {"nome":"","estilo":"casual"},
    "tts": {"engine":"kokoro","voz":"bf_emma","velocidade":1.1,
            "resumir_longas":True,"max_chars_falar":400},
    "stt": {"engine":"vosk","modelo_path":"models/vosk-model-pt",
            "silencio_timeout":1.5,"hotkey_toggle":"<ctrl>+<alt>+m"},
    "automacao": {"browser_padrao":"brave","permitir_pyautogui":True,"permitir_admin":True},
    "offline_mode": True,
    "log_level": "INFO",
}

def _load() -> dict:
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        def _merge(base, over):
            result = dict(base)
            for k, v in over.items():
                result[k] = _merge(base[k], v) if isinstance(v, dict) and k in base else v
            return result
        return _merge(_DEFAULTS, data)
    return dict(_DEFAULTS)

config: dict = _load()
