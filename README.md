# 🤖 Bingo - Assistente Pessoal Modular para Linux

**Bingo** é um assistente de voz e automação pessoal para Linux, construído com foco em arquitetura modular e privada. O sistema utiliza um **Core** central em Python que se comunica via **WebSockets** com múltiplos clientes — como aplicação Android (Jetpack Compose), linha de comando (CLI) e cliente de áudio.

---

## 🚀 Funcionalidades Principais

- 🎙️ **Reconhecimento de Voz Offline**: Transcrição local e privada utilizando `faster-whisper`.
- 🔌 **Servidor WebSocket Bidirecional**: Comunicação em tempo real entre o Core e os clientes, com suporte a *heartbeats* e reconexão automática.
- 💬 **Protocolo JSON & Normalização**: Parse de comandos de linguagem natural com tolerância a variações fonéticas via `rapidfuzz` e normalizador de texto.
- ⚡ **Dispatcher de Ações do Sistema**: Execução de comandos no Linux (abrir/fechar aplicações, controle de mídia, verificação de status).
- 📱 **Cliente Android Nativo**: App desenvolvido em Jetpack Compose com gravação de áudio, feedback sonoro e reconexão persistente.
- 💻 **Clientes CLI e Áudio**: Interfaces leves de terminal e clientes de teste para envio de áudio base64.

---

## 🏗️ Arquitetura do Sistema

```
                  ┌────────────────────────┐
                  │     Cliente Android    │
                  │   (Jetpack Compose)    │
                  └───────────┬────────────┘
                              │
  ┌─────────────────┐         │ (WebSockets / JSON Protocol)
  │   Cliente CLI   ├─────────┼─────────┐
  └─────────────────┘         │         │
                              ▼         ▼
                  ┌────────────────────────┐
                  │       Bingo Core       │
                  │   (Servidor Python)    │
                  └───────────┬────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
  │  Whisper STT  │   │   Normalizer  │   │  Dispatcher   │
  │   (Offline)   │   │  & Parser NLU │   │  & Actions    │
  └───────────────┘   └───────────────┘   └───────┬───────┘
                                                  │
                                                  ▼
                                       ┌─────────────────────┐
                                       │ Sistema Linux (OS)  │
                                       └─────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
bingo_project/
├── src/
│   └── bingo/
│       ├── actions/       # Ações do sistema (ping, status, comandos)
│       ├── client/        # Abstrações de cliente WebSocket
│       ├── network/       # Gerenciamento de sessões e heartbeat
│       ├── speech/        # Transcrição Whisper, recebimento e normalização
│       ├── dispatcher.py  # Despachante central de mensagens
│       ├── main.py        # Ponto de entrada do servidor Core
│       ├── parser.py      # Interpretador de comandos
│       ├── protocol.py    # Codificação/Decodificação do protocolo JSON
│       └── server.py      # Servidor WebSocket
├── clients/
│   ├── android/           # Aplicativo Android em Jetpack Compose
│   ├── audio/             # Cliente de teste para streaming de áudio
│   └── cli/               # Cliente interativo de linha de comando
├── docs/                  # Documentação de arquitetura, protocolo e roadmap
├── pyproject.toml         # Configuração e dependências (uv)
└── README.md
```

---

## 🛠️ Tecnologias Utilizadas

- **Core / Backend**: Python 3.14+, `uv`, `websockets`, `faster-whisper`, `rapidfuzz`
- **Cliente Android**: Kotlin, Jetpack Compose, OkHttp (WebSockets), Android AudioRecord
- **Ferramentas**: Git, Gradle

---

## ⚡ Como Executar

### Pró-requisitos

- Linux (Ubuntu/Debian, Arch, Fedora, etc.)
- Python 3.14 ou superior
- Gerenciador de pacotes [`uv`](https://github.com/astral-sh/uv)

### 1. Iniciar o Core (Servidor Bingo)

Instalar dependências:

```bash
uv sync
```

Iniciar o servidor WebSocket (por padrão escuta em `ws://0.0.0.0:8765`):

```bash
uv run python -m bingo.main
```

### 2. Executar o Cliente CLI

Em outro terminal, para interagir via texto:

```bash
uv run clients/cli/main.py
```

### 3. Executar o App Android

 Abra a pasta `clients/android` no **Android Studio** e execute o projeto no seu dispositivo ou emulador conectado à mesma rede local do servidor Bingo.

---

## 📚 Documentação Adicional

Consulte a pasta [`docs/`](file:///home/arthurdiaz/Documentos/zprojects/bingo_project/docs) para mais detalhes:
- 📄 [ARCHITECTURE.md](file:///home/arthurdiaz/Documentos/zprojects/bingo_project/docs/ARCHITECTURE.md) - Visão detalhada da arquitetura.
- 📄 [PROTOCOL.md](file:///home/arthurdiaz/Documentos/zprojects/bingo_project/docs/PROTOCOL.md) - Especificação do protocolo JSON via WebSocket.
- 📄 [ROADMAP.md](file:///home/arthurdiaz/Documentos/zprojects/bingo_project/docs/ROADMAP.md) - Status de desenvolvimento e próximas metas.

---

## 📝 Licença

Projeto desenvolvido por Arthur Diaz. Distribuído sob a licença MIT.