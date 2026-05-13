import re
from dataclasses import dataclass

_BLOCKED = {"regedit.exe","bcdedit.exe","format.com","cipher.exe","sc.exe","takeown.exe","icacls.exe"}
_DANGER  = re.compile(r'[;&|><`$\'"]')

@dataclass
class ValidationResult:
    ok: bool
    motivo: str = ""

def validar_target(t: str) -> ValidationResult:
    if not t or not t.strip(): return ValidationResult(False, "Alvo vazio.")
    if len(t) > 256:           return ValidationResult(False, "Alvo muito longo.")
    if _DANGER.search(t):      return ValidationResult(False, "Caractere perigoso.")
    if t.lower().strip() in _BLOCKED: return ValidationResult(False, f"'{t}' bloqueado por segurança.")
    return ValidationResult(True)
