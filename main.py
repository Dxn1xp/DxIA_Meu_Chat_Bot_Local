"""
Fluxo principal do programa:

inicia a IA
conecta voz/texto
cria o terminal interativo
recebe comandos
envia tudo pro Assistant
imprime respostas
controla desligamento

LEIA ISSO PLMDS: Esse arquivo cria a ponte da IA e Chatbot sem Interface (Por isso tem o api.py para a interface web).se conecta. Aqui é a interação do usuário, seja por texto ou voz. O menu de ajuda é uma referência rápida para os comandos disponíveis, e o status mostra informações sobre o sistema e a IA. O loop principal aguarda por entradas do usuário e processa cada comando. (Queria pode ensinar isso pra IA, mas nem sei muito de Machine Learning  :<)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
from core.assistant import Assistant
from utils.logger import get_logger

logger = get_logger(__name__)

_B = "\033[1m"; _C = "\033[96m"; _G = "\033[92m"
_R = "\033[91m"; _A = "\033[93m"; _X = "\033[0m"

"""DEIXAR AQUI APENAS SE QUISER TROCAR AS CORES DO TERMINAL
| Variável | Cor      |
| -------- | -------- |
| `_B`     | negrito  |
| `_C`     | ciano    |
| `_G`     | verde    |
| `_R`     | vermelho |
| `_A`     | amarelo  |
| `_X`     | reset    |

"""

AJUDA = f"""
{_B}━━━━ Automação ━━━━━━━━━━━━━━━━━━━━━━━━━━━━{_X}
  abrir <app>              qualquer app instalado
  abrir brave/chrome/...   browsers
  abrir youtube/gmail/...  sites diretos
  pesquisar <X>            Google
  pesquisar <X> no youtube YouTube
  fechar <app>             encerra (pede confirmação)
  minimizar tudo           minimiza todas as janelas
  mostrar desktop          Win+D
  screenshot               captura de tela
  o que está na tela       análise com IA de visão
  clicar em 500 300        clica nas coordenadas
  digitar <texto>          digita onde o cursor estiver

{_B}━━━━ Microfone ━━━━━━━━━━━━━━━━━━━━━━━━━━━━{_X}
  ativar escuta            microfone contínuo ON
  desativar escuta         microfone OFF
  voz                      ouve uma frase
  {_A}Toggle: Ctrl+Alt+M{_X}

{_B}━━━━ Personalidade ━━━━━━━━━━━━━━━━━━━━━━━━{_X}
  me chama de <nome>       define seu nome
  lembrar que <fato>       grava fato permanente
  mudar estilo formal      altera tom da IA
  fale mais devagar/rápido velocidade da voz

{_B}━━━━ Sistema ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{_X}
  timer de <N> minutos     alarme
  me lembra em <N> min de X lembrete
  volume <0-100>           ajusta volume
  brilho <0-100>           ajusta brilho
  listar processos         apps rodando
  status                   saúde do sistema
  monitor                  RAM e CPU
  memória                  o que sei sobre você
  histórico                últimas conversas
  ajuda                    este menu
  sair                     encerrar

{_A}Qualquer outra frase → IA responde{_X}
"""


async def main():
    com_voz   = "--voz" in sys.argv or "--continuo" in sys.argv
    continuo  = "--continuo" in sys.argv

    assistant = Assistant()
    await assistant.start(com_voz=com_voz)

    if continuo and assistant._stt and assistant._stt.available:
        loop = asyncio.get_event_loop()
        def _cb_voz(texto):
            print(f"\nVocê (voz): {texto}")
            asyncio.run_coroutine_threadsafe(
                _processar_voz(assistant, texto, loop), loop
            )
        assistant._stt.iniciar_modo_continuo(_cb_voz)

    try:
        await cli_loop(assistant, com_voz)
    except KeyboardInterrupt: #Se quiser sair com Ctrl+C mude isso. Prefiro assim.
        print("\n")
    finally:
        await assistant.stop()


async def _processar_voz(assistant, texto, loop):
    resp = await assistant.handle_input(texto, falar=True)
    if resp:
        print(f"\n{_B}Assistente:{_X} {resp}\n")


async def cli_loop(assistant: Assistant, com_voz: bool):
    info  = await assistant.status()
    nome  = assistant._memory.nome if assistant._memory else ""
    modo  = ("VOZ+" if com_voz else "") + ("CONTÍNUO" if "--continuo" in sys.argv else "TEXTO") #Se alterar algo aqui acaba com o desing que fiz com caracteres.

    print(f"\n{_B}╔══════════════════════════════════════════╗{_X}")
    print(f"{_B}║   DX_IA Assistant  v2.1                  ║{_X}")
    print(f"║   Modelo:  {info['model']:<30}║")
    print(f"║   Modo:    {modo:<30}║")
    print(f"║   TTS:     {info.get('tts_engine','—'):<30}║")
    adm = f"{_G}Sim{_X}" if info.get("admin") else "Não"
    print(f"║Admin:{adm:<39}║")
    print(f"{_B}╚══════════════════════════════════════════╝{_X}")
    print(f"  {'Olá, '+nome+'! ' if nome else ''}Digite 'ajuda' para ver os comandos.\n")

    while True:
        try:
            texto = input(f"{_C}Você:{_X} ").strip()
        except EOFError:
            break

        if not texto:
            continue
        lower = texto.lower()

        if lower in ("sair", "exit", "quit"):
            if assistant._tts and assistant._tts.available:
                assistant._tts.falar("Até logo!", bloquear=True)
            print("Até logo!")
            break

        if lower in ("ajuda", "help", "?"):
            print(AJUDA)
            continue

        if lower == "status":
            s = await assistant.status()
            online = f"{_G}online{_X}" if s["ollama_up"] else f"{_R}offline{_X}"
            pronto = f"{_G}pronto{_X}" if s["model_ready"] else f"{_R}erro{_X}"
            print(f"\n  Ollama:     {online}")
            print(f"  Modelo:     {s['model']} ({pronto})")
            print(f"  TTS:        {s.get('tts_engine','—')} {'ok' if s['tts'] else 'indisponível'}")
            print(f"  STT:        {'ok' if s['stt'] else 'indisponível'}")
            print(f"  Cache:      {s.get('cache_size',0)} entradas")
            print(f"  Admin:      {_G+'Sim'+_X if s.get('admin') else 'Não'}\n")
            continue

        if lower == "monitor":
            if assistant._monitor:
                print("\n" + assistant._monitor.relatorio() + "\n")
            continue

        if lower == "memória":
            if assistant._memory:
                print("\n" + assistant._memory.resumo() + "\n")
            continue

        if lower == "histórico":
            if assistant._history:
                msgs = assistant._history.recentes(10)
                print()
                for m in msgs:
                    pre = f"{_C}Você{_X}" if m["role"]=="user" else f"{_B}Assistente{_X}"
                    print(f"  [{m['ts'][11:16]}] {pre}: {m['content'][:80]}")
                print()
            continue

        if lower == "voz":
            if assistant._stt:
                print("Ouvindo...")
                t = assistant._stt.ouvir(timeout=6.0)
                if t:
                    print(f"Você (voz): {t}")
                    resp = await assistant.handle_input(t, falar=com_voz)
                    if resp:
                        print(f"\n{_B}Assistente:{_X} {resp}\n")
                else:
                    print("Não entendi.")
            else:
                print("STT não disponível.")
            continue

        #Analise da tela muito falho, mas deixei aqui pra mostrar a ideia. Se quiser usar, tem que instalar o pillow e outras coisas ai.
        if any(x in lower for x in ["o que está na tela", "analisar tela",
                                      "ver tela", "analisa a tela"]):
            print("Capturando tela...")
            from automation.screen_ai import ScreenAI
            sa = ScreenAI()
            resp = await sa.descrever_tela()
            print(f"\n{_B}Assistente:{_X} {resp}\n")
            continue

        if "erro na tela" in lower or "analisar erro" in lower:
            from automation.screen_ai import ScreenAI
            resp = await ScreenAI().analisar_erro()
            print(f"\n{_B}Assistente:{_X} {resp}\n")
            continue

        # Pipeline principal
        resp = await assistant.handle_input(texto, falar=com_voz)
        # Se for comando (sem usar a IA), resp é string — imprimir
        if resp is not None:
            print(f"\n{_B}Assistente:{_X} {resp}\n")


if __name__ == "__main__":
    asyncio.run(main())
