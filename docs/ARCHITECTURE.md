# Arquitetura

O Bingo é dividido em duas partes principais.

```
Clientes
│
├── CLI
├── Android
└── ESP32

        │
        ▼

═══════════════════════

        Core

═══════════════════════

Parser

↓

Dispatcher

↓

Actions

↓

Sistema Operacional
```

## Core

Responsável por:

- receber mensagens
- interpretar comandos
- executar ações
- responder aos clientes

O Core não conhece nenhum cliente específico.

## Clientes

Clientes apenas enviam mensagens JSON.

Exemplos:

- CLI
- Android
- ESP32

Todos utilizam o mesmo protocolo.

## Actions

Cada ação possui apenas uma responsabilidade.

Exemplos:

- abrir programa
- controlar volume
- fechar programa
- controlar mídia