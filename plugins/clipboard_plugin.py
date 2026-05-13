"""
plugins/clipboard_plugin.py — v2.1
Plugin que integra clipboard com IA:
  "resumir clipboard"     → resumo do texto copiado
  "traduzir clipboard"    → traduz para PT-BR
  "corrigir clipboard"    → corrige erros
  "melhorar clipboard"    → melhora o texto
  "copiar resposta"       → copia a última resposta para o clipboard
"""

import re
from plugins.base import Plugin, PluginMeta
from automation.clipboard import ClipboardManager
from utils.logger import get_logger

logger = get_logger(__name__)

_PADROES = [
    re.compile(r"resumir?\s+clipboard|resumir?\s+o\s+que\s+copiei", re.I),
    re.compile(r"traduzir?\s+clipboard", re.I),
    re.compile(r"corrigir?\s+clipboard|corrigir?\s+o\s+que\s+copiei", re.I),
    re.compile(r"melhorar?\s+clipboard|melhorar?\s+o\s+que\s+copiei", re.I),
    re.compile(r"o\s+que\s+(está|tem)\s+no\s+clipboard", re.I),
    re.compile(r"ler?\s+clipboard", re.I),
]


class ClipboardPlugin(Plugin):

    def __init__(self, ai_engine=None):
        self._clip = ClipboardManager()
        self._ai   = ai_engine  # referência ao AIEngine para processamento

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            nome="Clipboard",
            descricao="Lê, processa e escreve no clipboard com IA",
            exemplos=["resumir clipboard", "traduzir clipboard",
                      "corrigir o que copiei"],
        )

    def aceita(self, texto: str) -> bool:
        return any(p.search(texto) for p in _PADROES)

    async def executar(self, texto: str) -> str:
        conteudo = self._clip.ler()
        if not conteudo:
            return "Clipboard está vazio."

        lower = texto.lower()

        if re.search(r"o\s+que\s+(está|tem)|ler?", lower):
            preview = conteudo[:500]
            return f"Clipboard ({len(conteudo)} chars):\n{preview}" + \
                   ("..." if len(conteudo) > 500 else "")

        if not self._ai or not self._ai.model_ready:
            return f"IA não disponível. Clipboard tem: {conteudo[:200]}"

        # Determina a tarefa
        if "resumir" in lower:
            prompt = f"Resuma em 2-3 frases:\n\n{conteudo[:2000]}"
        elif "traduzir" in lower:
            prompt = f"Traduza para português do Brasil:\n\n{conteudo[:2000]}"
        elif "corrigir" in lower:
            prompt = (f"Corrija erros gramaticais e ortográficos. "
                      f"Retorne apenas o texto corrigido:\n\n{conteudo[:2000]}")
        elif "melhorar" in lower:
            prompt = (f"Melhore a clareza e fluidez deste texto. "
                      f"Retorne apenas o texto melhorado:\n\n{conteudo[:2000]}")
        else:
            prompt = f"O que é isso:\n\n{conteudo[:2000]}"

        resultado = await self._ai.ask(prompt, stream=False, cache=False)

        # Opcionalmente escreve o resultado de volta no clipboard
        if any(x in lower for x in ["corrigir", "melhorar", "traduzir"]):
            self._clip.escrever(resultado)
            return resultado + "\n\n(Resultado copiado para o clipboard)"

        return resultado
