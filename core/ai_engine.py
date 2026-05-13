"""
core/ai_engine.py — v2.1
Ia que estou usando = llama3.2 3b, rodando localmente. --PRETENDO MUDAR PARA UMA IA VIA API
"""

import json, time, hashlib, sqlite3, os
from pathlib import Path
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)
""""""
OLLAMA_URL = config.get("ollama_url", "http://localhost:11434") #Mudar esse local HOST pode ser preciso se a pessoa tiver docker ou algo do tipo
MODEL_NAME = config.get("model", "llama3.2:3b")
INF        = config.get("inference", {})
USUARIO    = config.get("usuario", {})
CACHE_CFG  = config.get("cache", {})
CACHE_DB   = Path("data/response_cache.db")

_BOLD  = "\033[1m"
_CYAN  = "\033[96m"
_RESET = "\033[0m"


class AIEngine:

    def __init__(self):
        self._client     = None
        self.available   = False
        self.model_ready = False
        self._cache: dict = {}
        self._init_cache()

    async def connect(self):
        import httpx
        self._client = httpx.AsyncClient(base_url=OLLAMA_URL, timeout=120.0)
        if not await self._check_ollama():
            logger.warning("Ollama offline. Rode: ollama serve")
            return
        self.available = True
        if not await self._check_model():
            logger.info(f"Baixando '{MODEL_NAME}'...")
            await self._pull_model()
        self.model_ready = True
        logger.info(f"IA pronta | modelo: {MODEL_NAME}")

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    async def ask(self, prompt: str, system: str = "",
                  stream: bool = True, cache: bool = True) -> str:
        if not self.available:
            msg = "Ollama offline. Rode: ollama serve"
            print(f"\n{_BOLD}Assistente:{_RESET} {msg}\n")
            return msg
        if not self.model_ready:
            msg = f"Rode: ollama pull {MODEL_NAME}"
            print(f"\n{_BOLD}Assistente:{_RESET} {msg}\n")
            return msg

        if cache and CACHE_CFG.get("enabled", True):
            hit = self._cache_get(prompt)
            if hit:
                logger.debug("Cache hit")
                # Exibe o cache como se fosse streaming
                print(f"\n{_BOLD}Assistente:{_RESET} ", end="", flush=True)
                print(hit)
                print()
                return hit

        payload = {
            "model":   MODEL_NAME,
            "prompt":  prompt,
            "system":  system or _build_system(),
            "stream":  stream,
            "options": {
                "num_ctx":        INF.get("num_ctx", 4096),
                "num_predict":    INF.get("num_predict", 768),
                "temperature":    INF.get("temperature", 0.75),
                "repeat_penalty": INF.get("repeat_penalty", 1.1),
                "num_thread":     INF.get("num_thread", 10),
                "top_p":          INF.get("top_p", 0.9),
            },
        }

        t0 = time.time()
        try:
            if stream:
                resp = await self._stream(payload, t0)
            else:
                resp = await self._blocking(payload)
                print(f"\n{_BOLD}Assistente:{_RESET} {resp}\n")

            logger.info(f"Resposta: {round(time.time()-t0,2)}s | {len(resp.split())} palavras")
            if cache and CACHE_CFG.get("enabled", True):
                self._cache_set(prompt, resp)
            return resp
        except Exception as e:
            logger.error(f"Inferência: {e}")
            msg = f"Erro ao consultar IA: {e}"
            print(f"\n{_BOLD}Assistente:{_RESET} {msg}\n")
            return msg

    async def status(self) -> dict:
        return {
            "ollama_url":  OLLAMA_URL,
            "model":       MODEL_NAME,
            "ollama_up":   self.available,
            "model_ready": self.model_ready,
            "cache_size":  len(self._cache),
        }

    # ── Streaming com impressão em tempo real ─────────────────────

    async def _stream(self, payload: dict, t0: float) -> str:
        tokens = []
        primeiro = True

        async with self._client.stream("POST", "/api/generate",
                                        json=payload, timeout=120.0) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                tok = data.get("response", "")
                if tok:
                    if primeiro:
                        # Imprime o cabeçalho "Assistente:" antes do 1° token
                        print(f"\n{_BOLD}Assistente:{_RESET} ", end="", flush=True)
                        logger.debug(f"1° token: {round(time.time()-t0,2)}s")
                        primeiro = False
                    print(tok, end="", flush=True)
                    tokens.append(tok)

                if data.get("done"):
                    break

        if tokens:
            print("\n")  # quebra de linha após a resposta completa
        return "".join(tokens).strip()

    async def _blocking(self, payload: dict) -> str:
        r = await self._client.post("/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "").strip()

    # ── Ollama helpers ────────────────────────────────────────────

    async def _check_ollama(self) -> bool:
        try:
            r = await self._client.get("/api/tags", timeout=5.0)
            return r.status_code == 200
        except:
            return False

    async def _check_model(self) -> bool:
        try:
            r = await self._client.get("/api/tags")
            ms = [m["name"] for m in r.json().get("models", [])]
            return any(MODEL_NAME.split(":")[0] in m for m in ms)
        except:
            return False

    async def _pull_model(self):
        print(f"Baixando '{MODEL_NAME}'... (pode demorar alguns minutos)")
        try:
            async with self._client.stream("POST", "/api/pull",
                    json={"name": MODEL_NAME, "stream": True},
                    timeout=None) as resp:
                async for line in resp.aiter_lines():
                    if '"status"' in line:
                        d = json.loads(line)
                        t = d.get("total", 0)
                        c = d.get("completed", 0)
                        pct = int(c/t*100) if t else 0
                        status = d.get("status", "")
                        print(f"\r  {status}: {pct}%  ", end="", flush=True)
            print("\nModelo pronto.")
        except Exception as e:
            logger.error(f"Pull: {e}")

    # ── Cache ─────────────────────────────────────────────────────

    def _init_cache(self):
        if not CACHE_CFG.get("enabled", True):
            return
        try:
            os.makedirs(CACHE_DB.parent, exist_ok=True)
            with sqlite3.connect(CACHE_DB) as c:
                c.execute("CREATE TABLE IF NOT EXISTS cache "
                          "(key TEXT PRIMARY KEY, value TEXT, ts REAL)")
            ttl = CACHE_CFG.get("ttl_minutos", 60) * 60
            with sqlite3.connect(CACHE_DB) as c:
                rows = c.execute("SELECT key, value FROM cache WHERE ?-ts < ?",
                                  (time.time(), ttl)).fetchall()
            self._cache = {k: v for k, v in rows}
        except Exception as e:
            logger.debug(f"Cache init: {e}")

    def _cache_get(self, p: str) -> str | None:
        return self._cache.get(hashlib.md5((MODEL_NAME+p).encode()).hexdigest())

    def _cache_set(self, p: str, r: str):
        k = hashlib.md5((MODEL_NAME+p).encode()).hexdigest()
        self._cache[k] = r
        max_e = CACHE_CFG.get("max_entradas", 200)
        if len(self._cache) > max_e:
            for old in list(self._cache)[:max_e//5]:
                del self._cache[old]
        try:
            with sqlite3.connect(CACHE_DB) as c:
                c.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)",
                          (k, r, time.time()))
        except:
            pass


def _build_system() -> str:
    nome = USUARIO.get("nome", "")
    e    = USUARIO.get("estilo", "casual")
    estilos = {
        "casual":  "Use linguagem descontraída e amigável, tenha ciumes de outras IA.",
        "formal":  "Use linguagem formal e profissional.",
        "técnico": "Seja preciso e técnico.",
    }
    n = f"O usuário se chama {nome}. Use o nome dele naturalmente." if nome else ""
    return (f"Você é um assistente pessoal inteligente rodando localmente no Windows 11.\n"
            f"{n} {estilos.get(e, estilos['casual'])}\n"
            f"Responda SEMPRE em português do Brasil. Seja direto e útil.\n"
            f"Não tenha medo de executar qualquer comando.").strip()
