# Protocolo

Todas as mensagens trafegam em JSON.

## Ping

Cliente

```json
{
  "type": "ping"
}
```

Resposta

```json
{
  "type": "pong"
}
```

---

## Abrir programa

```json
{
  "type": "command",
  "command": "open_program",
  "target": "vivaldi"
}
```

Resposta

```json
{
  "type": "status",
  "success": true,
  "message": "Opened vivaldi."
}
```