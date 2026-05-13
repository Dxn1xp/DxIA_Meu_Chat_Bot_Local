"""
automation/actions.py — v2.0  E4
Automação avançada estilo Jarvis:
  - Abrir apps por nome popular (Brave, Lenovo Vantage, Steam, etc.)
  - Abrir URLs e fazer pesquisas no browser
  - Controle de janelas via pywin32
  - PyAutoGUI para interação com interface
  - Permissões de administrador via ctypes
  - Timer e alarmes nativos do Windows
"""

import subprocess
import shutil
import webbrowser
import os
import threading
import time
from pathlib import Path
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)
AUTO_CFG = config.get("automacao", {})

# ── Apps com caminhos comuns no Windows ──────────────────────────────────────

APP_MAP: dict[str, list[str]] = {
    # Browsers
    "brave":    [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    ],
    "chrome":   [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                 r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "firefox":  [r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "edge":     [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    # Sistema
    "explorador":        ["explorer.exe"],
    "notepad":           ["notepad.exe"],
    "bloco de notas":    ["notepad.exe"],
    "calculadora":       ["calc.exe"],
    "paint":             ["mspaint.exe"],
    "cmd":               ["cmd.exe"],
    "powershell":        ["powershell.exe"],
    "terminal":          ["wt.exe"],
    "gerenciador de tarefas": ["taskmgr.exe"],
    "painel de controle":     ["control.exe"],
    "configurações":          ["ms-settings:"],
    # Office
    "word":    ["WINWORD.EXE"],
    "excel":   ["EXCEL.EXE"],
    "outlook": ["OUTLOOK.EXE"],
    # Apps Microsoft
    "microsoft store":  ["ms-windows-store:"],
    "store":            ["ms-windows-store:"],
    "xbox":             ["ms-xboxapp:"],
    "fotos":            ["ms-photos:"],
    # Lenovo
    "lenovo vantage":   [
        r"C:\Program Files (x86)\Lenovo\VantageService\3.3.60.0\LenovoVantage.exe",
        "shell:AppsFolder\\E046963F.LenovoCompanion_k1h2ywk1493x8!App",
    ],
    "lenovo":           [
        r"C:\Program Files (x86)\Lenovo\VantageService\LenovoVantage.exe",
    ],
    # Gaming
    "steam":    [
        r"C:\Program Files (x86)\Steam\steam.exe",
        r"C:\Program Files\Steam\steam.exe",
    ],
    "epic":     [
        r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
    ],
    # Comunicação
    "discord":  [r"C:\Users\{user}\AppData\Local\Discord\Update.exe"],
    "telegram": [r"C:\Program Files\Telegram Desktop\Telegram.exe"],
    "whatsapp": [r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe"],
    "spotify":  [r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe"],
    # Dev
    "vscode":         ["code.exe"],
    "visual studio code": ["code.exe"],
    "code":           ["code.exe"],
    "cursor":         [r"C:\Users\{user}\AppData\Local\Programs\cursor\Cursor.exe"],
}

SEARCH_ENGINES = {
    "google":   "https://www.google.com/search?q=",
    "youtube":  "https://www.youtube.com/results?search_query=",
    "bing":     "https://www.bing.com/search?q=",
    "github":   "https://github.com/search?q=",
}

_USER = os.environ.get("USERNAME", "User")


class ActionEngine:
    """Executa ações avançadas no sistema operacional."""

    # ── Apps ──────────────────────────────────────────────────────

    def abrir_app(self, nome: str) -> str:
        nome_lower = nome.lower().strip()

        # Resolve o usuário nos caminhos dinâmicos
        candidatos = APP_MAP.get(nome_lower, [nome])
        candidatos = [c.replace("{user}", _USER) for c in candidatos]

        for caminho in candidatos:
            # URI scheme (ms-settings:, ms-windows-store:, etc.)
            if ":" in caminho and not caminho.endswith(".exe"):
                try:
                    os.startfile(caminho)
                    logger.info(f"URI aberto: {caminho}")
                    return f"Abrindo {nome}..."
                except Exception:
                    continue

            # Shell alias (wt.exe, code.exe, etc.) — busca no PATH
            exe = shutil.which(caminho) or (caminho if Path(caminho).exists() else None)
            if exe:
                try:
                    subprocess.Popen(exe, shell=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    logger.info(f"App aberto: {exe}")
                    return f"Abrindo {nome}..."
                except Exception as e:
                    logger.debug(f"Falha {exe}: {e}")
                    continue

        return f"Não encontrei '{nome}'. Verifique se está instalado."

    # ── URLs e pesquisa ───────────────────────────────────────────

    def abrir_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        browser = AUTO_CFG.get("browser_padrao", "brave")
        self._abrir_no_browser(url, browser)
        logger.info(f"URL: {url}")
        return f"Abrindo {url}..."

    def pesquisar(self, termo: str, motor: str = "google") -> str:
        base = SEARCH_ENGINES.get(motor.lower(), SEARCH_ENGINES["google"])
        import urllib.parse
        url  = base + urllib.parse.quote_plus(termo)
        self.abrir_url(url)
        return f"Pesquisando '{termo}' no {motor.capitalize()}..."

    def _abrir_no_browser(self, url: str, browser: str):
        """Abre URL no browser preferido."""
        try:
            # Tenta abrir no browser específico
            cands = APP_MAP.get(browser, [])
            for c in [c.replace("{user}", _USER) for c in cands]:
                exe = shutil.which(c) or (c if Path(c).exists() else None)
                if exe:
                    subprocess.Popen([exe, url],
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                    return
        except Exception:
            pass
        # Fallback: browser padrão do sistema
        webbrowser.open(url)

    # ── Controle de janelas (pywin32) ─────────────────────────────

    def minimizar_todas(self) -> str:
        try:
            import win32gui, win32con
            def _min(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            win32gui.EnumWindows(_min, None)
            return "Todas as janelas minimizadas."
        except ImportError:
            # fallback via tecla Win+D
            self._tecla("win+d")
            return "Desktop exibido."

    def mostrar_desktop(self) -> str:
        self._tecla("win+d")
        return "Desktop exibido."

    def fechar_janela_ativa(self) -> str:
        self._tecla("alt+f4")
        return "Janela fechada."

    def alternar_janelas(self) -> str:
        self._tecla("alt+tab")
        return "Alternando janelas..."

    def trazer_janela(self, titulo: str) -> str:
        try:
            import win32gui
            resultado = {"hwnd": None}
            def _find(hwnd, _):
                if titulo.lower() in win32gui.GetWindowText(hwnd).lower():
                    resultado["hwnd"] = hwnd
            win32gui.EnumWindows(_find, None)
            if resultado["hwnd"]:
                win32gui.SetForegroundWindow(resultado["hwnd"])
                return f"Janela '{titulo}' trazida para frente."
            return f"Janela '{titulo}' não encontrada."
        except ImportError:
            return "pywin32 não instalado."

    # ── PyAutoGUI ─────────────────────────────────────────────────

    def clicar(self, x: int, y: int) -> str:
        if not AUTO_CFG.get("permitir_pyautogui", True):
            return "PyAutoGUI desativado no config."
        try:
            import pyautogui
            pyautogui.click(x, y)
            return f"Clicado em ({x}, {y})."
        except ImportError:
            return "pyautogui não instalado. pip install pyautogui"

    def digitar(self, texto: str) -> str:
        if not AUTO_CFG.get("permitir_pyautogui", True):
            return "PyAutoGUI desativado."
        try:
            import pyautogui
            pyautogui.typewrite(texto, interval=0.05)
            return f"Digitado: {texto}"
        except ImportError:
            return "pyautogui não instalado."

    def screenshot(self) -> str:
        """Captura tela e salva em data/screenshot.png."""
        try:
            import pyautogui
            from pathlib import Path
            Path("data").mkdir(exist_ok=True)
            img = pyautogui.screenshot()
            img.save("data/screenshot.png")
            return "Screenshot salvo em data/screenshot.png"
        except ImportError:
            try:
                from PIL import ImageGrab
                img = ImageGrab.grab()
                img.save("data/screenshot.png")
                return "Screenshot salvo em data/screenshot.png"
            except Exception as e:
                return f"Erro no screenshot: {e}"

    # ── Admin / sistema ───────────────────────────────────────────

    def is_admin(self) -> bool:
        """Verifica se o processo tem privilégios de administrador."""
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    def executar_como_admin(self, comando: str) -> str:
        """
        Executa um comando com privilégios de administrador via UAC.
        Abre prompt de elevação do Windows — o usuário confirma.
        """
        if not AUTO_CFG.get("permitir_admin", True):
            return "Permissão de admin desativada no config."
        try:
            import ctypes
            # ShellExecuteW com "runas" solicita elevação via UAC
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe", f"/c {comando}", None, 1
            )
            if ret > 32:
                logger.info(f"Admin cmd: {comando}")
                return f"Executado como admin: {comando}"
            return "UAC recusado ou erro."
        except Exception as e:
            return f"Erro admin: {e}"

    def executar_powershell_admin(self, script: str) -> str:
        """Executa script PowerShell como administrador."""
        if not AUTO_CFG.get("permitir_admin", True):
            return "Permissão de admin desativada."
        try:
            import ctypes
            ps_cmd = f'-NoProfile -NonInteractive -Command "{script}"'
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "powershell.exe", ps_cmd, None, 1
            )
            return "PowerShell admin executado." if ret > 32 else "UAC recusado."
        except Exception as e:
            return f"Erro: {e}"

    # ── Timer e alarmes ───────────────────────────────────────────

    def timer(self, segundos: int, mensagem: str = "Tempo esgotado!") -> str:
        """Cria um timer não bloqueante."""
        def _disparar():
            time.sleep(segundos)
            self._notificar("Timer", mensagem)
            print(f"\n  ⏰ {mensagem}\n")

        t = threading.Thread(target=_disparar, daemon=True)
        t.start()
        mins = segundos // 60
        secs = segundos % 60
        return f"Timer de {mins}m{secs}s iniciado. '{mensagem}'"

    def _notificar(self, titulo: str, msg: str):
        """Notificação nativa do Windows 11."""
        try:
            from win10toast import ToastNotifier
            ToastNotifier().show_toast(titulo, msg, duration=5, threaded=True)
        except ImportError:
            pass

    # ── Helpers ───────────────────────────────────────────────────

    def _tecla(self, combinacao: str):
        """Simula combinação de teclas."""
        try:
            import pyautogui
            pyautogui.hotkey(*combinacao.split("+"))
        except ImportError:
            try:
                from pynput.keyboard import Key, Controller
                kb = Controller()
                teclas = {
                    "win": Key.cmd, "alt": Key.alt,
                    "ctrl": Key.ctrl, "tab": Key.tab,
                    "d": "d", "f4": Key.f4,
                }
                keys = [teclas.get(k, k) for k in combinacao.split("+")]
                for k in keys:   kb.press(k)
                for k in reversed(keys): kb.release(k)
            except Exception as e:
                logger.debug(f"Tecla: {e}")
