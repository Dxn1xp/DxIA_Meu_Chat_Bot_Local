"""
automation/clipboard.py — v2.1
Integração com clipboard do Windows.
Permite ler, escrever e processar com IA o conteúdo copiado.
"""

from utils.logger import get_logger
logger = get_logger(__name__)


class ClipboardManager:

    def ler(self) -> str:
        """Retorna o conteúdo atual do clipboard."""
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except TypeError:
                data = ""
            finally:
                win32clipboard.CloseClipboard()
            return str(data).strip()
        except ImportError:
            return self._ler_fallback()
        except Exception as e:
            logger.error(f"Clipboard ler: {e}")
            return ""

    def escrever(self, texto: str) -> bool:
        """Escreve texto no clipboard."""
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(texto, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return True
        except ImportError:
            return self._escrever_fallback(texto)
        except Exception as e:
            logger.error(f"Clipboard escrever: {e}")
            return False

    def limpar(self) -> bool:
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            return False

    def _ler_fallback(self) -> str:
        """Fallback usando tkinter quando pywin32 não disponível."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            content = root.clipboard_get()
            root.destroy()
            return content
        except Exception:
            return ""

    def _escrever_fallback(self, texto: str) -> bool:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(texto)
            root.update()
            root.after(500, root.destroy)
            root.mainloop()
            return True
        except Exception:
            return False
