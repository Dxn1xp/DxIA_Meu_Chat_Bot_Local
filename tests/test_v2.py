"""tests/test_v2.py — Testes do assistente v2"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest

def test_parser_mic_on():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("ativar escuta")
    assert c and c.action == "mic_on"

def test_parser_mic_off():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("desativar microfone")
    assert c and c.action == "mic_off"

def test_parser_open_brave():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("abrir o brave")
    assert c and c.action == "open_app"

def test_parser_open_url():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("abrir youtube.com")
    assert c and c.action == "open_url"

def test_parser_search_google():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("pesquisar inteligência artificial")
    assert c and c.action == "search"
    assert "inteligência" in c.args.get("termo","")

def test_parser_search_youtube():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("pesquisar lofi no youtube")
    assert c and c.action == "search"
    assert c.args.get("motor") == "youtube"

def test_parser_timer_min():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("timer de 5 minutos")
    assert c and c.action == "timer_min"
    assert c.args["segundos"] == 300

def test_parser_screenshot():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("screenshot")
    assert c and c.action == "screenshot"

def test_parser_set_name():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("me chama de Denilson")
    assert c and c.action == "set_name"

def test_parser_minimize_all():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("minimizar tudo")
    assert c and c.action == "minimize_all"

def test_parser_alias_youtube():
    from core.command_parser import CommandParser
    p = CommandParser()
    c = p.parse("abrir youtube")
    assert c and c.action == "open_url"
    assert "youtube" in c.target

def test_memory_set_get(tmp_path, monkeypatch):
    import system.memory as mod
    monkeypatch.setattr(mod, "DB", tmp_path / "mem.db")
    from system.memory import UserMemory
    m = UserMemory()
    m.set("nome", "Denilson")
    assert m.get("nome") == "Denilson"

def test_memory_fatos(tmp_path, monkeypatch):
    import system.memory as mod
    monkeypatch.setattr(mod, "DB", tmp_path / "mem.db")
    from system.memory import UserMemory
    m = UserMemory()
    m.lembrar_fato("gosta de café")
    fatos = m.fatos_recentes()
    assert any("café" in f for f in fatos)

def test_validator_ok():
    from utils.validator import validar_target
    assert validar_target("brave.exe").ok is True

def test_validator_blocked():
    from utils.validator import validar_target
    assert validar_target("regedit.exe").ok is False

def test_validator_injection():
    from utils.validator import validar_target
    assert validar_target("app; rm -rf /").ok is False

def test_tts_unavailable_by_default():
    from voice.tts import TTSEngine
    t = TTSEngine()
    assert t.available is False
    t.falar("teste")  # não deve crashar

def test_stt_unavailable_by_default():
    from voice.stt import STTEngine
    s = STTEngine()
    assert s.available is False
    assert s.ouvir(timeout=0.1) is None


# ── Plugins v2 ────────────────────────────────────────────────────────────────

def test_plugin_registry_vazio():
    from plugins.base import PluginRegistry
    r = PluginRegistry()
    assert "Nenhum" in r.listar()

@pytest.mark.asyncio
async def test_plugin_registry_despachar_none():
    from plugins.base import PluginRegistry
    r = PluginRegistry()
    assert await r.despachar("qualquer coisa") is None

def test_system_plugin_aceita():
    from plugins.system_plugin import SystemPlugin
    p = SystemPlugin()
    assert p.aceita("qual é o meu ip local") is True
    assert p.aceita("espaço no disco") is True
    assert p.aceita("temperatura cpu") is True
    assert p.aceita("abrir chrome") is False

def test_clipboard_plugin_aceita():
    from plugins.clipboard_plugin import ClipboardPlugin
    p = ClipboardPlugin()
    assert p.aceita("resumir clipboard") is True
    assert p.aceita("o que tem no clipboard") is True
    assert p.aceita("abrir spotify") is False


# ── Voice loop ────────────────────────────────────────────────────────────────

def test_voice_loop_instancia():
    from voice.voice_loop import VoiceLoop
    v = VoiceLoop()
    assert v.ativo is False

def test_voice_loop_parar_sem_iniciar():
    from voice.voice_loop import VoiceLoop
    v = VoiceLoop()
    v.parar()  # não deve lançar exceção


# ── Clipboard ─────────────────────────────────────────────────────────────────

def test_clipboard_instancia():
    from automation.clipboard import ClipboardManager
    c = ClipboardManager()
    assert c is not None


# ── Notifications ─────────────────────────────────────────────────────────────

def test_notifications_importa():
    from automation.notifications import notificar
    assert callable(notificar)


# ── Screen AI ─────────────────────────────────────────────────────────────────

def test_screen_ai_instancia():
    from automation.screen_ai import ScreenAI
    s = ScreenAI()
    assert s._disponivel is None  # não verificado ainda
