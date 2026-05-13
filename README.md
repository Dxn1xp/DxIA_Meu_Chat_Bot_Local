# DxIA_Meu_Chat_Bot_Local


ChatBot que roda localmente o modelo llama3.2 3b. 

Funcional apenas no Windows 11.

Pode resolver questões tanto por texto quanto por voz usando o comando --voz, Ou apenas falando. O comando de Voz Sempre Ativa pode ser alternado com (Control + Alt + M).

Capaz de fazer algumas tarefas no Windows com comandos que podem ser listados digitando o comando (ajuda) no terminal. 



Algumas funções:

Abrir Apps, Fechar Apps, Abrir Navegadores, Abrir Youtube, Pesquisar, Pesquisar no Youtube, Minimizar tudo, Mostrar Desktop, Tirar Print, Descrever o que está na tela, Apagar luz dos cômodos (No caso é necessário a tecnologia conectada ao Script "Light-Controls.py" localizado em automation)

Outras funções:

Timer, Controle de Volume, Controle de Brilho, Listar Processos, Status da IA, Monitor de RAM e CPU, Ajuda, Mudar estilo (Formal ou Descontraído), Velocidade de fala, e Configuração de nome do usuário.

Qualquer coisa a ser perguntada sem citar um comando > IA vai responder no chat.




Requisitos:
Python 3.13+ (Eu uso 3.14)
Node.js
Ollama instalado

Modelo: llama3.2 3b. 


Dependências:


### Backend
- Python
- Flask
- Ollama
- OpenCV
- MediaPipe


Instale a maioria usando esses comandos:

pip install PyYAML==6.0.2
pip install httpx==0.27.0
pip install psutil==6.0.0
pip install pytest==8.2.2
pip install pytest-asyncio==0.23.8
pip install pyttsx3==2.90
pip install sounddevice==0.4.6
pip install soundfile==0.12.1
pip install numpy
pip install edge-tts==6.1.12
pip install pynput==1.7.7
pip install pyautogui==0.9.54
pip install pywin32==308
pip install vosk

--------------------------------------

### Frontend
- React
- Vite

-------------------------------------

# Instalação

## Backend

cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

python api.py
 
---

## Frontend

cd frontend

npm install
npm run dev

