"""
plugins/system_plugin.py — v2.1
Plugin PowerShell seguro + informações do sistema.
Whitelist de comandos aprovados — NUNCA executa scripts arbitrários.
"""

import re, subprocess
from plugins.base import Plugin, PluginMeta

_CMDS: list[tuple[re.Pattern, str, bool]] = [
    (re.compile(r"ip\s*(local|meu|da\s*máquina)?", re.I),
     "(Get-NetIPAddress -AddressFamily IPv4 | Where {$_.InterfaceAlias -notlike '*Loopback*'}).IPAddress",
     False),
    (re.compile(r"bateria|carga\s*do\s*notebook", re.I),
     "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining",
     False),
    (re.compile(r"espaço\s*(em\s*|no\s*|)(disco|hd|ssd|c:)", re.I),
     "Get-PSDrive C | ForEach {\"Usado: $([math]::Round($_.Used/1GB,1))GB | Livre: $([math]::Round($_.Free/1GB,1))GB\"}",
     False),
    (re.compile(r"uptime|tempo\s*(ligado|online|rodando)", re.I),
     "(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime | ForEach {\"Uptime: $($_.Days)d $($_.Hours)h $($_.Minutes)m\"}",
     False),
    (re.compile(r"(?:última|ultima)\s*atualização|windows\s*update", re.I),
     "Get-HotFix | Sort InstalledOn -Desc | Select -First 3 | Format-Table HotFixID,InstalledOn -Auto",
     False),
    (re.compile(r"temperatura\s*(cpu|processador)", re.I),
     "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace 'root/wmi' | ForEach {\"Temp: $([math]::Round($_.CurrentTemperature/10-273.15,1))°C\"}",
     False),
    (re.compile(r"limpar\s*(temp|temporários?|arquivos\s*temp)", re.I),
     "Remove-Item -Path $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue; 'Temporários removidos.'",
     True),
    (re.compile(r"reiniciar\s*(pc|computador|windows)", re.I),
     "Restart-Computer -Force",
     True),
    (re.compile(r"desligar\s*(pc|computador|windows)", re.I),
     "Stop-Computer -Force",
     True),
    (re.compile(r"versão\s*(do\s*)?(windows|sistema)", re.I),
     "(Get-WmiObject Win32_OperatingSystem).Caption",
     False),
    (re.compile(r"ram\s*total|memória\s*total", re.I),
     "[math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)",
     False),
]


class SystemPlugin(Plugin):

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            nome="Sistema",
            descricao="Informações do sistema via PowerShell (whitelist segura)",
            exemplos=["ip local", "bateria", "espaço no disco", "uptime",
                      "temperatura cpu", "versão do windows"],
        )

    def aceita(self, texto: str) -> bool:
        return any(p.search(texto) for p, _, _ in _CMDS)

    async def executar(self, texto: str) -> str:
        for pattern, script, confirmar in _CMDS:
            if pattern.search(texto):
                if confirmar:
                    resp = input(f"\n  ⚠  PowerShell: {script[:60]}...\n  Confirmar? (s/N): ")
                    if resp.strip().lower() not in ("s","sim","y","yes"):
                        return "Ação cancelada."
                return self._run(script)
        return "Comando não reconhecido."

    def _run(self, script: str) -> str:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True, text=True, timeout=15,
                encoding="utf-8", errors="replace",
            )
            saida = (r.stdout or r.stderr or "").strip()
            return saida if saida else "Executado (sem saída)."
        except subprocess.TimeoutExpired:
            return "PowerShell: timeout."
        except Exception as e:
            return f"Erro PowerShell: {e}"
