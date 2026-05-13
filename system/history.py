"""
system/history.py — v2.1
Histórico de conversas em SQLite com contexto para IA.
"""

import sqlite3, os
from pathlib import Path
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)
DB = Path("data/history.db")


class ConversationHistory:

    def __init__(self):
        os.makedirs(DB.parent, exist_ok=True)
        with sqlite3.connect(DB) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS msgs (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      TEXT, role TEXT, content TEXT,
                tipo    TEXT DEFAULT 'chat'
            )""")

    def salvar(self, role: str, content: str, tipo: str = "chat"):
        try:
            with sqlite3.connect(DB) as c:
                c.execute("INSERT INTO msgs (ts,role,content,tipo) VALUES (?,?,?,?)",
                          (datetime.now().isoformat(), role, content, tipo))
        except Exception as e:
            logger.error(f"History save: {e}")

    def recentes(self, n: int = 20) -> list[dict]:
        try:
            with sqlite3.connect(DB) as c:
                rows = c.execute(
                    "SELECT ts,role,content,tipo FROM msgs ORDER BY id DESC LIMIT ?", (n,)
                ).fetchall()
            return [{"ts":r[0],"role":r[1],"content":r[2],"tipo":r[3]}
                    for r in reversed(rows)]
        except:
            return []

    def contexto_para_ia(self, n: int = 4) -> str:
        msgs = self.recentes(n * 2)
        if not msgs: return ""
        return "\n".join(
            f"{'Usuário' if m['role']=='user' else 'Assistente'}: {m['content'][:200]}"
            for m in msgs
        )

    def estatisticas(self) -> dict:
        try:
            with sqlite3.connect(DB) as c:
                total = c.execute("SELECT COUNT(*) FROM msgs").fetchone()[0]
                cmds  = c.execute("SELECT COUNT(*) FROM msgs WHERE tipo='command'").fetchone()[0]
            return {"total": total, "comandos": cmds}
        except:
            return {}
