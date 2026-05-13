"""
system/memory.py — v2.0  E5
Memória de longo prazo:
  - Nome e preferências do usuário
  - Fatos importantes ditos pelo usuário
  - Estilo de comunicação aprendido
  - Todas as preferências persistidas em SQLite
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger
from utils.config import config

logger = get_logger(__name__)
DB = Path("data/memory.db")


class UserMemory:
    """Persiste e recupera memórias do usuário."""

    def __init__(self):
        os.makedirs(DB.parent, exist_ok=True)
        self._init_db()
        # Carrega preferências iniciais do config
        self._sincronizar_config()

    def _init_db(self):
        with sqlite3.connect(DB) as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS preferencias (
                    chave TEXT PRIMARY KEY,
                    valor TEXT,
                    ts    TEXT
                );
                CREATE TABLE IF NOT EXISTS fatos (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    fato    TEXT NOT NULL,
                    contexto TEXT,
                    ts      TEXT
                );
            """)

    def _sincronizar_config(self):
        """Usa config.yaml como base, mas memória tem prioridade."""
        usuario = config.get("usuario", {})
        nome_config = usuario.get("nome", "")
        if nome_config and not self.get("nome"):
            self.set("nome", nome_config)

    # ── Preferências ──────────────────────────────────────────────

    def get(self, chave: str, padrao: str = "") -> str:
        try:
            with sqlite3.connect(DB) as c:
                row = c.execute("SELECT valor FROM preferencias WHERE chave=?",
                                (chave,)).fetchone()
            return row[0] if row else padrao
        except: return padrao

    def set(self, chave: str, valor: str) -> None:
        try:
            with sqlite3.connect(DB) as c:
                c.execute("INSERT OR REPLACE INTO preferencias VALUES (?,?,?)",
                          (chave, valor, datetime.now().isoformat()))
            logger.info(f"Memória: {chave} = {valor!r}")
        except Exception as e:
            logger.error(f"Memória set: {e}")

    # ── Fatos ────────────────────────────────────────────────────

    def lembrar_fato(self, fato: str, contexto: str = "") -> None:
        """Grava um fato importante sobre o usuário."""
        try:
            with sqlite3.connect(DB) as c:
                c.execute("INSERT INTO fatos (fato, contexto, ts) VALUES (?,?,?)",
                          (fato, contexto, datetime.now().isoformat()))
            logger.info(f"Fato registrado: {fato!r}")
        except Exception as e:
            logger.error(f"Fato: {e}")

    def fatos_recentes(self, n: int = 5) -> list[str]:
        try:
            with sqlite3.connect(DB) as c:
                rows = c.execute(
                    "SELECT fato FROM fatos ORDER BY id DESC LIMIT ?", (n,)
                ).fetchall()
            return [r[0] for r in rows]
        except: return []

    # ── Propriedades de acesso rápido ────────────────────────────

    @property
    def nome(self) -> str:
        return self.get("nome", "")

    @nome.setter
    def nome(self, v: str):
        self.set("nome", v)

    @property
    def estilo(self) -> str:
        return self.get("estilo", config.get("usuario", {}).get("estilo", "casual"))

    @estilo.setter
    def estilo(self, v: str):
        self.set("estilo", v)

    @property
    def vel_tts(self) -> float:
        return float(self.get("vel_tts",
                              str(config.get("tts", {}).get("velocidade", 1.1))))

    @vel_tts.setter
    def vel_tts(self, v: float):
        self.set("vel_tts", str(v))

    def para_prompt(self) -> str:
        """Retorna contexto de memória para enriquecer o system prompt."""
        partes = []
        nome = self.nome
        if nome:
            partes.append(f"O usuário se chama {nome}.")
        fatos = self.fatos_recentes(3)
        if fatos:
            partes.append("Fatos sobre o usuário: " + " | ".join(fatos))
        estilo_map = {
            "casual":  "Use linguagem descontraída e amigável.",
            "formal":  "Use linguagem formal e profissional.",
            "técnico": "Seja preciso e técnico.",
        }
        partes.append(estilo_map.get(self.estilo, estilo_map["casual"]))
        return "\n".join(partes)

    def resumo(self) -> str:
        """Exibe as memórias armazenadas."""
        linhas = ["Memórias do assistente:"]
        nome = self.nome
        linhas.append(f"  Nome: {nome or '(não definido)'}")
        linhas.append(f"  Estilo: {self.estilo}")
        linhas.append(f"  Vel. TTS: {self.vel_tts}x")
        fatos = self.fatos_recentes(5)
        if fatos:
            linhas.append("  Fatos:")
            for f in fatos:
                linhas.append(f"    • {f}")
        return "\n".join(linhas)
