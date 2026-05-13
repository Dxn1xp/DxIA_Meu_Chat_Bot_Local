"""
core/command_parser.py — v2.0
Parser expandido com novos comandos E3/E4/E5:
  - Controle de microfone
  - Abrir apps, URLs, pesquisas
  - Controle de janelas
  - Timer e alarme
  - Personalidade e memória
"""

import re
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Command:
    action:           str
    target:           str  = ""
    args:             dict = field(default_factory=dict)
    requires_confirm: bool = False


_RAW = [
    # ── Microfone E3 ────────────────────────────────────────────
    (r"(?<!des)ativar\s+(escuta|microfone|mic)",      "mic_on",      False),
    (r"desativar\s+(escuta|microfone|mic)",           "mic_off",     False),
    (r"(silenciar|mutar|mudo)",                       "mic_off",     False),

    # ── URLs primeiro (mais específico que open_app) ──────────────
    (r"abr[ia]r?\s+(https?://\S+)",                     "open_url",    False),
    (r"abr[ia]r?\s+([\w\-]+\.[a-z]{2,}(?:/\S*)?)",  "open_url",    False),

    # ── Abrir apps E4 ───────────────────────────────────────────
    (r"abr[ia]r?\s+o?\s*brave",                       "open_app",    False),
    (r"abr[ia]r?\s+o?\s*steam",                       "open_app",    False),
    (r"abr[ia]r?\s+o?\s*lenovo\s*vantage",            "open_app",    False),
    (r"abr[ia]r?\s+(?:a?\s*)microsoft\s*store",       "open_app",    False),
    (r"abr[ia]r?\s+o?\s*spotify",                     "open_app",    False),
    (r"abr[ia]r?\s+o?\s*discord",                     "open_app",    False),
    (r"abr[ia]r?\s+o?\s*(.+)",                        "open_app",    False),
    (r"iniciar\s+o?\s*(.+)",                          "open_app",    False),
    (r"lançar\s+o?\s*(.+)",                           "open_app",    False),

    # ── URLs e pesquisa E4 ──────────────────────────────────────
    (r"(?:pesquisar?|buscar?|procurar?)\s+(.+)\s+no\s+(google|youtube|bing|github)",
                                                       "search",      False),
    (r"(?:pesquisar?|buscar?|procurar?)\s+(.+)",      "search",      False),
    (r"abr[ia]r?\s+o?\s*youtube",                     "open_url",    False),

    # ── Fechar / encerrar ───────────────────────────────────────
    (r"fechar?\s+(?:o?\s*)(.+)",                      "close_app",   True),
    (r"encerrar?\s+(?:o?\s*)(.+)",                    "close_app",   True),
    (r"matar?\s+(.+)",                                "close_app",   True),

    # ── Controle de janelas E4 ──────────────────────────────────
    (r"minimizar?\s+(?:tudo|todas)",                  "minimize_all",False),
    (r"mostrar?\s+(?:desktop|área\s*de\s*trabalho)",  "show_desktop",False),
    (r"fechar?\s+(?:janela|essa\s*janela)",            "close_window",False),
    (r"(?:alt[\s+]tab|alternar\s+janelas?)",          "alt_tab",     False),
    (r"trazer?\s+(.+)\s+(?:para\s*frente|à\s*frente)","focus_window",False),

    # ── PyAutoGUI E4 ────────────────────────────────────────────
    (r"clicar?\s+(?:em\s+)?(\d+)[,\s]+(\d+)",        "click",       False),
    (r"digitar?\s+(.+)",                              "type_text",   False),
    (r"screenshot|captura\s*de\s*tela",               "screenshot",  False),

    # ── Timer E4 ────────────────────────────────────────────────
    (r"(?:timer|cronômetro)\s+(?:de\s+)?(\d+)\s*(?:minutos?|min)",  "timer_min", False),
    (r"(?:timer|cronômetro)\s+(?:de\s+)?(\d+)\s*(?:segundos?|seg)", "timer_seg", False),
    (r"me?\s+lembrar?\s+(?:em|daqui)\s+(\d+)\s*(minutos?|segundos?)\s*(?:de\s+)?(.+)?",
                                                      "reminder",    False),

    # ── Admin E4 ────────────────────────────────────────────────
    (r"executar?\s+(?:como\s+)?admin(?:istrador)?\s+(.+)", "run_admin", True),

    # ── Sistema ─────────────────────────────────────────────────
    (r"volume\s+(\d+)",                               "set_volume",  False),
    (r"brilho\s+(\d+)",                               "set_brightness", False),
    (r"listar?\s+processos?",                         "list_processes", False),

    # ── Personalidade E5 ────────────────────────────────────────
    (r"me\s+chama(?:r)?\s+de\s+(.+)",                "set_name",    False),
    (r"meu\s+nome\s+é\s+(.+)",                       "set_name",    False),
    (r"(?:usar?|mudar?)\s+estilo\s+(.+)",             "set_estilo",  False),
    (r"(?:fala|fale)\s+mais\s+(devagar|rápido|lento)","set_vel_tts", False),
]

_PATTERNS = [(re.compile(p, re.I | re.U), a, c) for p, a, c in _RAW]

# Aliases especiais por padrão de texto completo
_ALIAS_EXATO: dict[str, Command] = {
    "abrir youtube":   Command("open_url", "https://youtube.com"),
    "abrir gmail":     Command("open_url", "https://gmail.com"),
    "abrir whatsapp":  Command("open_url", "https://web.whatsapp.com"),
    "abrir github":    Command("open_url", "https://github.com"),
    "abrir netflix":   Command("open_url", "https://netflix.com"),
}


class CommandParser:

    def __init__(self):
        self.patterns = _PATTERNS

    def parse(self, texto: str) -> Command | None:
        texto = texto.strip()
        lower = texto.lower()

        # Verificar aliases exatos primeiro
        if lower in _ALIAS_EXATO:
            return _ALIAS_EXATO[lower]

        for pattern, action, confirm in self.patterns:
            m = pattern.search(texto)
            if m:
                groups = m.groups()
                target = groups[0].strip() if groups else ""
                args   = {}

                # Parser específico por ação
                if action == "search":
                    args["termo"] = groups[0].strip() if groups else ""
                    args["motor"] = groups[1].strip() if len(groups) > 1 else "google"
                    target = args["termo"]

                elif action in ("timer_min", "timer_seg"):
                    n = int(groups[0]) if groups else 0
                    args["segundos"] = n * 60 if action == "timer_min" else n
                    target = str(args["segundos"])

                elif action == "reminder":
                    n    = int(groups[0]) if groups else 1
                    unit = groups[1] if len(groups) > 1 else "minutos"
                    msg  = groups[2].strip() if len(groups) > 2 and groups[2] else "Lembrete!"
                    args["segundos"] = n * 60 if "min" in unit else n
                    args["mensagem"] = msg
                    target = msg

                elif action == "click" and len(groups) >= 2:
                    args["x"] = int(groups[0])
                    args["y"] = int(groups[1])
                    target = f"{args['x']},{args['y']}"

                logger.debug(f"Comando: {action} | target={target!r}")
                return Command(action=action, target=target,
                               args=args, requires_confirm=confirm)
        return None
