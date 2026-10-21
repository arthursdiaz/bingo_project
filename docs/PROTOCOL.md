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

---

## Reproduzir Playlist / Música

Cliente

```json
{
  "type": "command",
  "command": "play_music",
  "playlist_url": "https://music.youtube.com/playlist?list=YOUR_PLAYLIST_ID",
  "shuffle": true,
  "device": "TutuLola"
}
```

Resposta

```json
{
  "type": "status",
  "success": true,
  "message": "Playlist aberta com modo aleatório no Vivaldi (sessão Premium preservada). Chromecast 'TutuLola' confirmado ativo em 192.168.0.5..."
}
```