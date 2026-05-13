"""
core/assistant.py — v2.1 final
Integra: E1 cache/modelo, E2 Kokoro TTS, E3 mic contínuo, E4 automação,
         E5 personalidade, E6 plugins, clipboard, notificações, voice_loop.
"""

from core.ai_engine      import AIEngine
from core.command_parser import CommandParser
from automation.actions  import ActionEngine
from utils.logger        import get_logger
from utils.config        import config

logger = get_logger(__name__)


class Assistant:

    def __init__(self):
        self.ai      = AIEngine()
        self.parser  = CommandParser()
        self.actions = ActionEngine()
        # Módulos opcionais
        self._tts        = None
        self._stt        = None
        self._voice_loop = None
        self._memory     = None
        self._history    = None
        self._monitor    = None
        self._plugins    = None
        self._clipboard  = None

    async def start(self, com_voz: bool = False, continuo: bool = False):
        logger.info("Iniciando Windows AI Assistant v2.1...")
        self._carregar_memoria()
        self._carregar_historico()
        self._carregar_monitor()
        self._carregar_plugins()
        self._carregar_clipboard()
        await self.ai.connect()
        if com_voz or continuo:
            self._carregar_voz()
        if continuo and self._voice_loop:
            self._iniciar_voice_loop()
        if self._tts and self._tts.available:
            nome = self._memory.nome if self._memory else ""
            self._tts.falar(f"Olá{', '+nome if nome else ''}! Pronto.", bloquear=True)
        logger.info("Pronto.")

    async def stop(self):
        if self._voice_loop: self._voice_loop.parar()
        if self._stt: self._stt.parar_modo_continuo()
        if self._tts: self._tts.parar()
        if self._monitor: self._monitor.parar()
        await self.ai.disconnect()
        logger.info("Encerrado.")

    # ── Pipeline principal ────────────────────────────────────────

    async def handle_input(self, texto: str, falar: bool = False) -> str | None:
        if self._history:
            self._history.salvar("user", texto)

        # Memória E5
        resp_mem = self._handle_memoria(texto)
        if resp_mem:
            return self._responder(resp_mem, falar)

        # Plugins (clipboard, sistema, etc.)
        if self._plugins:
            resp_plugin = await self._plugins.despachar(texto)
            if resp_plugin:
                return self._responder(resp_plugin, falar)

        # Comandos do parser
        cmd = self.parser.parse(texto)
        if cmd:
            resp = await self._executar_comando(cmd, falar)
            return self._responder(resp, falar)

        # IA — streaming imprime diretamente
        system = self._build_system()
        resposta = await self.ai.ask(texto, system=system, stream=True)
        if self._history and resposta:
            self._history.salvar("assistant", resposta)
        if falar and self._tts and self._tts.available and resposta:
            self._tts.falar(resposta)
        return None

    async def handle_voz(self) -> str | None:
        if not self._stt or not self._stt.available:
            return "STT não disponível."
        print("Ouvindo...")
        texto = self._stt.ouvir(timeout=6.0)
        if not texto: return "Não entendi."
        print(f"Você (voz): {texto}")
        await self.handle_input(texto, falar=True)
        return texto

    # ── Executor de comandos ──────────────────────────────────────

    async def _executar_comando(self, cmd, falar: bool) -> str:
        from utils.validator import validar_target
        import psutil, asyncio

        a = cmd.action

        # Microfone E3
        if a == "mic_on":
            if self._stt and self._stt.available:
                loop = asyncio.get_event_loop()
                def _cb(t):
                    print(f"\nVocê (voz): {t}")
                    asyncio.run_coroutine_threadsafe(
                        self.handle_input(t, falar=True), loop)
                self._stt.iniciar_modo_continuo(_cb)
                return "Microfone ativado. Pode falar!"
            return "STT não disponível. Instale Vosk."

        if a == "mic_off":
            if self._stt: self._stt.parar_modo_continuo()
            return "Microfone desativado."

        # Automação E4
        if a == "open_app":
            v = validar_target(cmd.target)
            return self.actions.abrir_app(cmd.target) if v.ok else f"Bloqueado: {v.motivo}"

        if a == "open_url":   return self.actions.abrir_url(cmd.target)

        if a == "search":
            return self.actions.pesquisar(
                cmd.args.get("termo", cmd.target), cmd.args.get("motor","google"))

        if a == "close_app":
            if cmd.requires_confirm and not self._confirmar(cmd):
                return "Cancelado."
            nome = cmd.target.lower().replace(".exe","")
            mortos = []
            for p in psutil.process_iter(["name","pid"]):
                try:
                    if nome in (p.info["name"] or "").lower():
                        p.terminate(); mortos.append(p.info["name"])
                except: pass
            return (f"Encerrado: {', '.join(set(mortos))}"
                    if mortos else f"'{cmd.target}' não encontrado.")

        # Janelas
        if a == "minimize_all":  return self.actions.minimizar_todas()
        if a == "show_desktop":  return self.actions.mostrar_desktop()
        if a == "close_window":  return self.actions.fechar_janela_ativa()
        if a == "alt_tab":       return self.actions.alternar_janelas()
        if a == "focus_window":  return self.actions.trazer_janela(cmd.target)

        # GUI
        if a == "click":    return self.actions.clicar(cmd.args.get("x",0), cmd.args.get("y",0))
        if a == "type_text":return self.actions.digitar(cmd.target)
        if a == "screenshot":return self.actions.screenshot()

        # Timer/lembrete
        if a in ("timer_min","timer_seg"):
            return self.actions.timer(int(cmd.args.get("segundos",60)))
        if a == "reminder":
            return self.actions.timer(int(cmd.args.get("segundos",60)),
                                       cmd.args.get("mensagem","Lembrete!"))

        # Admin
        if a == "run_admin": return self.actions.executar_como_admin(cmd.target)

        # Clipboard
        if a == "clipboard_read":
            if self._clipboard:
                c = self._clipboard.ler()
                return f"Clipboard: {c[:300]}" if c else "Clipboard vazio."

        if a == "clipboard_write":
            if self._clipboard:
                self._clipboard.escrever(cmd.target)
                return "Copiado para o clipboard."

        # Sistema
        if a == "set_volume":
            nivel = max(0, min(100, int(cmd.target)))
            import subprocess
            ps = (f"$wsh=New-Object -ComObject WScript.Shell;"
                  f"1..50|%{{$wsh.SendKeys([char]174)}};"
                  f"$s=[math]::Round({nivel}/2);1..$s|%{{$wsh.SendKeys([char]175)}}")
            subprocess.run(["powershell","-Command",ps], capture_output=True)
            return f"Volume → {nivel}%"

        if a == "set_brightness":
            nivel = max(0, min(100, int(cmd.target)))
            import subprocess
            subprocess.run(["powershell","-Command",
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1,{nivel})"], capture_output=True)
            return f"Brilho → {nivel}%"

        if a == "list_processes":
            _sys = {"system","registry","smss.exe","csrss.exe","wininit.exe",
                    "services.exe","lsass.exe","svchost.exe","dwm.exe"}
            nomes = sorted({p.info["name"] for p in psutil.process_iter(["name"])
                            if p.info["name"] and
                            p.info["name"].lower() not in _sys and
                            p.info["name"].endswith(".exe")})[:20]
            return "Processos:\n" + "\n".join(f"  • {n}" for n in nomes)

        return f"Ação '{a}' não implementada."

    # ── Memória E5 ────────────────────────────────────────────────

    def _handle_memoria(self, texto: str) -> str | None:
        if not self._memory: return None
        import re
        lower = texto.lower().strip()
        m = re.search(r"me\s+chama(?:r)?\s+de\s+(.+)", lower)
        if not m: m = re.search(r"meu\s+nome\s+[eé]\s+(.+)", lower)
        if m:
            nome = m.group(1).strip().title()
            self._memory.nome = nome
            return f"Anotado! Vou te chamar de {nome}."
        m = re.search(r"(?:usar?|mudar?)\s+estilo\s+(formal|casual|técnico)", lower)
        if m:
            self._memory.estilo = m.group(1)
            return f"Estilo: '{m.group(1)}'."
        if "fale mais devagar" in lower or "mais lento" in lower:
            self._memory.vel_tts = max(0.6, self._memory.vel_tts - 0.2)
            return f"Mais devagar ({self._memory.vel_tts:.1f}x)."
        if "fale mais rápido" in lower:
            self._memory.vel_tts = min(2.0, self._memory.vel_tts + 0.2)
            return f"Mais rápido ({self._memory.vel_tts:.1f}x)."
        m = re.search(r"lembr[ae]r?\s+que\s+(.+)", lower)
        if m:
            fato = m.group(1).strip()
            self._memory.lembrar_fato(fato)
            return f"Guardado: '{fato}'"
        return None

    def _build_system(self) -> str:
        base = ("Você é um assistente pessoal inteligente no Windows 11. "
                "Responda SEMPRE em português do Brasil. Seja direto e útil.")
        extras = []
        if self._memory:
            ctx = self._memory.para_prompt()
            if ctx: extras.append(ctx)
        if self._history:
            hist = self._history.contexto_para_ia(4)
            if hist: extras.append(f"Histórico:\n{hist}")
        return base + ("\n\n" + "\n\n".join(extras) if extras else "")

    def _responder(self, texto: str, falar: bool) -> str:
        if self._history: self._history.salvar("assistant", texto)
        if falar and self._tts and self._tts.available:
            self._tts.falar(texto)
        return texto

    def _confirmar(self, cmd) -> bool:
        print(f"\n  ⚠  Confirmar: {cmd.action} → {cmd.target}")
        return input("  (s/N): ").strip().lower() in ("s","sim","y","yes")

    async def status(self) -> dict:
        ai = await self.ai.status()
        return {
            **ai,
            "parser_patterns": len(self.parser.patterns),
            "stt":             bool(self._stt and self._stt.available),
            "tts":             bool(self._tts and self._tts.available),
            "tts_engine":      getattr(self._tts, "_engine_nome", "—"),
            "plugins":         len(self._plugins) if self._plugins else 0,
            "memoria":         bool(self._memory),
            "admin":           self.actions.is_admin(),
            "voice_loop":      bool(self._voice_loop and self._voice_loop.ativo),
        }

    # ── Carregadores ──────────────────────────────────────────────

    def _carregar_memoria(self):
        try:
            from system.memory import UserMemory
            self._memory = UserMemory()
        except Exception as e: logger.warning(f"Memória: {e}")

    def _carregar_historico(self):
        try:
            from system.history import ConversationHistory
            self._history = ConversationHistory()
        except Exception as e: logger.warning(f"Histórico: {e}")

    def _carregar_monitor(self):
        try:
            from system.monitor import ResourceMonitor
            self._monitor = ResourceMonitor()
            self._monitor.iniciar()
        except Exception as e: logger.warning(f"Monitor: {e}")

    def _carregar_plugins(self):
        try:
            from plugins.base import PluginRegistry
            from plugins.system_plugin import SystemPlugin
            from plugins.clipboard_plugin import ClipboardPlugin
            self._plugins = PluginRegistry()
            self._plugins.registrar(SystemPlugin())
            self._plugins.registrar(ClipboardPlugin(self.ai))
            logger.info(f"Plugins: {len(self._plugins)} carregados.")
        except Exception as e: logger.warning(f"Plugins: {e}")

    def _carregar_clipboard(self):
        try:
            from automation.clipboard import ClipboardManager
            self._clipboard = ClipboardManager()
        except Exception as e: logger.warning(f"Clipboard: {e}")

    def _carregar_voz(self):
        try:
            from voice.tts import TTSEngine
            from voice.stt import STTEngine
            self._tts = TTSEngine()
            self._stt = STTEngine()
            self._tts.load()
            self._stt.load()
        except Exception as e: logger.warning(f"Voz: {e}")

    def _iniciar_voice_loop(self):
        """E6-01: inicia voz em processo separado."""
        try:
            from voice.voice_loop import VoiceLoop
            import asyncio
            cfg = config.get("stt", {})
            self._voice_loop = VoiceLoop(
                modelo_path=cfg.get("modelo_path", "models/vosk-model-pt"),
                silencio=float(cfg.get("silencio_timeout", 1.5)),
            )
            loop = asyncio.get_event_loop()
            def _cb(texto):
                print(f"\nVocê (voz): {texto}")
                asyncio.run_coroutine_threadsafe(
                    self.handle_input(texto, falar=True), loop)
            ok = self._voice_loop.iniciar(_cb)
            if not ok:
                logger.warning("VoiceLoop falhou — usando STT padrão.")
                if self._stt and self._stt.available:
                    self._stt.iniciar_modo_continuo(_cb)
        except Exception as e:
            logger.warning(f"VoiceLoop: {e}")
