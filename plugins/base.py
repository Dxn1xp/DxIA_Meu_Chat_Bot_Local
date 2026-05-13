"""
plugins/base.py — v2.1
Sistema de plugins para o assistente v2.
Mais simples que v1: foca em detecção por palavras-chave e execução async.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PluginMeta:
    nome:        str
    descricao:   str
    versao:      str = "1.0.0"
    exemplos:    list[str] = field(default_factory=list)


class Plugin(ABC):

    @property
    @abstractmethod
    def meta(self) -> PluginMeta: ...

    @abstractmethod
    def aceita(self, texto: str) -> bool: ...

    @abstractmethod
    async def executar(self, texto: str) -> str: ...

    def ativar(self) -> bool:
        return True

    def desativar(self) -> None:
        pass


class PluginRegistry:

    def __init__(self):
        self._plugins: list[Plugin] = []

    def registrar(self, plugin: Plugin) -> bool:
        try:
            if plugin.ativar():
                self._plugins.append(plugin)
                logger.info(f"Plugin: {plugin.meta.nome} v{plugin.meta.versao}")
                return True
            logger.warning(f"Plugin não ativado: {plugin.meta.nome}")
            return False
        except Exception as e:
            logger.error(f"Plugin {plugin.meta.nome}: {e}")
            return False

    async def despachar(self, texto: str) -> str | None:
        for p in self._plugins:
            if p.aceita(texto):
                try:
                    return await p.executar(texto)
                except Exception as e:
                    logger.error(f"Plugin {p.meta.nome}: {e}")
                    return f"Erro no plugin {p.meta.nome}: {e}"
        return None

    def listar(self) -> str:
        if not self._plugins:
            return "Nenhum plugin carregado."
        return "Plugins:\n" + "\n".join(
            f"  • {p.meta.nome} — {p.meta.descricao}" for p in self._plugins
        )

    def __len__(self): return len(self._plugins)
