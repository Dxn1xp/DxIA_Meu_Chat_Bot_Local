"""
api.py — Servidor HTTP para o DX_IA
Assistant via REST API para o frontend web.

IMPORTANTE: Este arquivo NÃO substitui o Main.py (Eu só chamei o que estava no main.py por que não queria mudar o main.py quando fui integrar o frontend.)
  - Main.py  → interface de linha de comando (CLI)
  - api.py   → interface web (browser)

Como iniciar:
    python api.py (em terminal separado do Ollama)
    Ollama serve

Endpoints:
    GET  /health  - verifica se o servidor está ok
    GET  /status  -  status completo do Assistant
    POST /chat    - envia mensagem, recebe resposta da IA
"""

import sys
from pathlib import Path

# ── Garante que o diretório raiz está no sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
import threading
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from core.assistant import Assistant
from utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────
# Configuração do Flask
# ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# O Assistant é assíncrono (async/await). Para integrá-lo ao Flask
# (síncrono), mantemos um loop asyncio rodando em thread separada
_loop:      asyncio.AbstractEventLoop | None = None
_assistant: Assistant | None = None
_ready      = threading.Event()   # sinaliza quando o Assistant estiver pronto


def _iniciar_loop_async():
    """Roda em thread separada: cria loop, inicia Assistant e fica vivo."""
    global _loop, _assistant

    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)

    async def _setup():
        global _assistant
        _assistant = Assistant()
        await _assistant.start(com_voz=False)   # sem TTS/STT no modo web
        _ready.set()
        logger.info("Assistant iniciado no modo web.")

    _loop.run_until_complete(_setup())
    _loop.run_forever()


# Inicia a thread do Assistant ao importar o módulo
_thread = threading.Thread(target=_iniciar_loop_async, daemon=True, name="assistant-loop")
_thread.start()


def _run_async(coro):
    """Executa uma corrotina no loop dedicado e aguarda o resultado (bloqueante)."""
    if _loop is None:
        raise RuntimeError("Loop asyncio não inicializado.")
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=30)   # timeout de 30s por requisição



@app.route("/", methods=["GET"])
def raiz():
    """Confirmação rápida de que o servidor está no ar."""
    return jsonify({
        "servico":  "Windows AI Assistant — API Web",
        "versao":   "2.1",
        "status":   "online",
        "timestamp": datetime.datetime.now().isoformat(),
    })


@app.route("/health", methods=["GET"])
def health():
    """Health-check usado pelo frontend para colorir o indicador de status."""
    pronto = _ready.is_set()
    return jsonify({"status": "healthy" if pronto else "starting"}), 200 if pronto else 503


@app.route("/status", methods=["GET"])
def status():
    """Retorna o status detalhado do Assistant (modelo, TTS, STT, etc.)."""
    if not _ready.is_set():
        return jsonify({"erro": "Assistant ainda iniciando..."}), 503

    try:
        dados = _run_async(_assistant.status())
        return jsonify(dados)
    except Exception as e:
        logger.error(f"[/status] {e}")
        return jsonify({"erro": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """
    Endpoint principal de chat.

    Recebe:
        { "mensagem": "texto do usuário" }

    Retorna:
        {
            "resposta":  "texto da IA",
            "status":    "ok",
            "timestamp": "..."
        }
    """
    # Aguarda o Assistant ficar pronto (Se o pc for uma bomba aumente o valor maximo de 15 segundos.)
    if not _ready.wait(timeout=15):
        return jsonify({
            "erro":   "Assistant ainda iniciando. Tente novamente em instantes.",
            "status": "starting",
        }), 503

    #Payload Validação
    dados = request.get_json(silent=True)
    if not dados or "mensagem" not in dados:
        return jsonify({"erro": "Campo 'mensagem' obrigatório.", "status": "erro"}), 400

    mensagem = dados["mensagem"].strip()
    if not mensagem:
        return jsonify({"erro": "Mensagem não pode ser vazia.", "status": "erro"}), 400

    # ── Processa via Assistant ──────────────────────────────────────────
    try:
        
        resposta = _run_async(_assistant.handle_input(mensagem, falar=False))

       
        if resposta is None:
            resposta = "Comando executado com sucesso."

        return jsonify({
            "resposta":  resposta,
            "status":    "ok",
            "timestamp": datetime.datetime.now().isoformat(),
        })

    except TimeoutError:
        logger.error("[/chat] Timeout ao processar mensagem.")
        return jsonify({"erro": "Tempo limite excedido. O modelo pode estar lento.", "status": "erro"}), 504

    except Exception as e:
        logger.error(f"[/chat] Erro inesperado: {e}")
        return jsonify({"erro": "Erro interno no servidor.", "status": "erro"}), 500



if __name__ == "__main__":
    print("=" * 52)
    print("  Windows AI Assistant — Servidor Web")
    print("  URL:      http://localhost:5000") #Mude o localhost se precisar, mas ai tem que mudar no React lá no frontend também.
    print("  Chat:     POST /chat")
    print("  Status:   GET  /status")
    print("  Health:   GET  /health")
    print("  Aguardando Assistant iniciar...")
    print("=" * 52)

    # use_reloader=False para o Flask não iniciar feito louco.
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,       # mantenha False; o loop dedicado não é thread-safe com reloader
        use_reloader=False,
    )
