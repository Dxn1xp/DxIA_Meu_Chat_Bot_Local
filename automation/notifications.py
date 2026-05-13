"""
automation/notifications.py — v2.1
Notificações nativas do Windows 11 com múltiplos fallbacks.
Prioridade: win11toast → win10toast → PowerShell → MessageBox
"""

import subprocess
from utils.logger import get_logger
logger = get_logger(__name__)


def notificar(titulo: str, mensagem: str,
              duracao: int = 5, som: bool = True) -> bool:
    """
    Exibe notificação nativa do Windows.
    Retorna True se exibida com sucesso.
    """
    # 1. win11toast — melhor para Windows 11
    try:
        from win11toast import notify
        notify(titulo, mensagem, duration=duracao)
        return True
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"win11toast: {e}")

    # 2. win10toast
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(titulo, mensagem,
                                    duration=duracao, threaded=True)
        return True
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"win10toast: {e}")

    # 3. PowerShell BurntToast (nativo Windows 11)
    try:
        ps = (
            f"$Text1 = [Windows.UI.Notifications.ToastTemplateType, Windows.UI.Notifications, "
            f"ContentType = WindowsRuntime]::ToastText01;"
            f"$Template = [Windows.UI.Notifications.ToastNotificationManager, "
            f"Windows.UI.Notifications, ContentType = WindowsRuntime]"
            f"::GetTemplateContent($Text1);"
            f"$RawXml = [xml] $Template.GetXml();"
            f"($RawXml.toast.visual.binding.text | Where {{$_.id -eq '1'}}).AppendChild("
            f"$RawXml.CreateTextNode('{mensagem}')) | Out-Null;"
            f"$SerializedXml = New-Object Windows.Data.Xml.Dom.XmlDocument;"
            f"$SerializedXml.LoadXml($RawXml.OuterXml);"
            f"$Toast = [Windows.UI.Notifications.ToastNotification, "
            f"Windows.UI.Notifications, ContentType = WindowsRuntime]::new($SerializedXml);"
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            f"ContentType = WindowsRuntime]::CreateToastNotifier('{titulo}').Show($Toast);"
        )
        subprocess.run(["powershell", "-Command", ps],
                       capture_output=True, timeout=5)
        return True
    except Exception as e:
        logger.debug(f"PS toast: {e}")

    # 4. Fallback: beep + print no terminal
    if som:
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            pass
    print(f"\n  🔔 {titulo}: {mensagem}\n")
    return False
