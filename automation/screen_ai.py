"""
automation/screen_ai.py — v2.1  E4-05
Captura de tela + análise por modelo de visão local (moondream2 via Ollama).
Permite perguntar "o que está na minha tela?" e receber resposta inteligente.

Modelo recomendado: moondream (pequeno, ~1.7B, rápido)
  ollama pull moondream

Uso:
  from automation.screen_ai import ScreenAI
  sa = ScreenAI()
  desc = await sa.descrever_tela()
  resp = await sa.perguntar_sobre_tela("qual é o erro que aparece?")
"""

import base64, io, os
from pathlib import Path
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)

OLLAMA_URL   = config.get("ollama_url", "http://localhost:11434")
VISION_MODEL = "moondream"   # leve e rápido; alternativa: llava:7b


class ScreenAI:
    """Captura tela e usa modelo de visão para interpretar."""

    def __init__(self):
        self._disponivel = None  # None = não verificado ainda

    async def descrever_tela(self) -> str:
        """Captura a janela ativa e pede ao modelo para descrevê-la."""
        return await self.perguntar_sobre_tela(
            "Descreva em português o que aparece nesta tela. "
            "Seja conciso e objetivo."
        )

    async def perguntar_sobre_tela(self, pergunta: str) -> str:
        """Captura tela e envia junto com a pergunta ao modelo de visão."""
        img_b64 = self._capturar_base64()
        if not img_b64:
            return "Não consegui capturar a tela."

        if not await self._verificar_modelo():
            return (f"Modelo de visão '{VISION_MODEL}' não disponível.\n"
                    f"  Instale com: ollama pull {VISION_MODEL}")

        return await self._consultar_visao(img_b64, pergunta)

    async def analisar_erro(self) -> str:
        """Especializado em detectar erros na tela."""
        return await self.perguntar_sobre_tela(
            "Há algum erro, aviso ou mensagem de problema visível nesta tela? "
            "Se sim, descreva exatamente o que diz. Se não, diga 'Sem erros visíveis'."
        )

    # ── Internos ──────────────────────────────────────────────────

    def _capturar_base64(self) -> str | None:
        """Captura a tela e retorna como base64 PNG."""
        try:
            import pyautogui
            img = pyautogui.screenshot()
        except ImportError:
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
            except Exception as e:
                logger.error(f"Screenshot: {e}")
                return None

        # Redimensiona para 1280x720 max (economiza tokens)
        img.thumbnail((1280, 720))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def _verificar_modelo(self) -> bool:
        if self._disponivel is not None:
            return self._disponivel
        try:
            import httpx
            async with httpx.AsyncClient(base_url=OLLAMA_URL, timeout=5.0) as c:
                r = await c.get("/api/tags")
                models = [m["name"] for m in r.json().get("models", [])]
                self._disponivel = any(VISION_MODEL in m for m in models)
        except:
            self._disponivel = False
        return self._disponivel

    async def _consultar_visao(self, img_b64: str, pergunta: str) -> str:
        try:
            import httpx
            async with httpx.AsyncClient(base_url=OLLAMA_URL, timeout=60.0) as c:
                r = await c.post("/api/generate", json={
                    "model":  VISION_MODEL,
                    "prompt": pergunta,
                    "images": [img_b64],
                    "stream": False,
                    "options": {"num_predict": 300, "temperature": 0.3},
                })
                return r.json().get("response", "Sem resposta.").strip()
        except Exception as e:
            logger.error(f"Visão: {e}")
            return f"Erro ao analisar tela: {e}"
