import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

import websockets

from bingo.server import handle_client, music_lock
from bingo.protocol import MessageType, parse_message, encode_message


class TestServerMusicIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Inicia servidor de teste em porta efêmera aleatória
        self.server = await websockets.serve(handle_client, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]
        self.uri = f"ws://127.0.0.1:{self.port}"
        # Garante que o lock de música esteja liberado no início de cada teste
        if music_lock.locked():
            try:
                music_lock.release()
            except RuntimeError:
                pass

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        if music_lock.locked():
            try:
                music_lock.release()
            except RuntimeError:
                pass

    async def test_ping_pong(self):
        """Valida que o ping continua funcionando normalmente."""
        async with websockets.connect(self.uri) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            response = await asyncio.wait_for(ws.recv(), timeout=2.0)
            data = json.loads(response)
            self.assertEqual(data.get("type"), "pong")

    async def test_existing_command_open_program(self):
        """Valida que comandos existentes retornam status verdadeiro sem serem engolidos."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = MagicMock()
            async with websockets.connect(self.uri) as ws:
                req = {
                    "type": "command",
                    "command": "open_program",
                    "target": "vivaldi",
                    "id": "cmd-123"
                }
                await ws.send(json.dumps(req))
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(response)
                self.assertEqual(data.get("type"), "status")
                self.assertTrue(data.get("success"))
                self.assertEqual(data.get("id"), "cmd-123")
                self.assertIn("Opened vivaldi", data.get("message"))

    @patch("bingo.actions.music.play_playlist")
    async def test_play_music_command_success(self, mock_play):
        """Valida envio de comando musical: recebe in_progress e depois sucesso real."""
        mock_play.return_value = {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": "Playlist iniciada no Vivaldi e transmissão Cast nativa CONFIRMADA para o Chromecast 'TutuLola'",
            "local_playback": {"status": "routed_to_cast", "track": "Song Title"},
            "cast_stream": {
                "status": "active",
                "confirmed": True,
                "session_type": "native_ytm",
                "app_id": "2DB7CC49",
                "display_name": "YouTube Music",
                "device": "TutuLola",
                "persistent": True,
            },
        }

        async with websockets.connect(self.uri) as ws:
            req = {
                "type": "command",
                "command": "play_music",
                "device": "TutuLola",
                "id": "music-req-1"
            }
            await ws.send(json.dumps(req))

            # 1. Resposta intermediária de execução assíncrona iniciada
            raw_ack = await asyncio.wait_for(ws.recv(), timeout=2.0)
            ack = json.loads(raw_ack)
            self.assertEqual(ack.get("type"), "status")
            self.assertEqual(ack.get("status"), "in_progress")
            self.assertEqual(ack.get("command"), "play_music")
            self.assertEqual(ack.get("id"), "music-req-1")

            # 2. Resposta final com a confirmação real da reprodução
            raw_final = await asyncio.wait_for(ws.recv(), timeout=3.0)
            final_res = json.loads(raw_final)
            self.assertEqual(final_res.get("type"), "status")
            self.assertTrue(final_res.get("success"))
            self.assertEqual(final_res.get("id"), "music-req-1")
            self.assertIn("data", final_res)
            self.assertEqual(final_res["data"]["mode"], "cdp_cast_confirmed")
            self.assertEqual(final_res["data"]["cast_stream"]["device"], "TutuLola")

    @patch("bingo.actions.music.play_playlist")
    async def test_music_message_type_success(self, mock_play):
        """Valida que mensagens com type='music' também são roteadas corretamente para music.execute."""
        mock_play.return_value = {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": "Transmissão confirmada",
            "local_playback": {"status": "routed_to_cast", "track": "Faixa 1"},
            "cast_stream": {"status": "active", "confirmed": True, "device": "TutuLola"},
        }

        async with websockets.connect(self.uri) as ws:
            req = {
                "type": "music",
                "device": "TutuLola",
                "id": "type-music-2"
            }
            await ws.send(json.dumps(req))

            raw_ack = await asyncio.wait_for(ws.recv(), timeout=2.0)
            ack = json.loads(raw_ack)
            self.assertEqual(ack.get("status"), "in_progress")

            raw_final = await asyncio.wait_for(ws.recv(), timeout=3.0)
            final_res = json.loads(raw_final)
            self.assertTrue(final_res.get("success"))
            self.assertEqual(final_res.get("id"), "type-music-2")

    @patch("bingo.actions.music.play_playlist")
    async def test_play_music_chromecast_busy(self, mock_play):
        """Valida detecção de Chromecast ocupado por outro app (ex: Netflix)."""
        mock_play.return_value = {
            "success": False,
            "mode": "cdp_cast_busy_other_app",
            "message": "O Chromecast 'TutuLola' está ocupado executando outro aplicativo (Netflix [CA5E8412]).",
            "local_playback": {"status": "playing", "track": "None"},
            "cast_stream": {
                "status": "busy_other_app",
                "confirmed": False,
                "app_id": "CA5E8412",
                "display_name": "Netflix",
                "device": "TutuLola",
            },
        }

        async with websockets.connect(self.uri) as ws:
            req = {
                "type": "command",
                "command": "play_music",
                "id": "busy-test-3"
            }
            await ws.send(json.dumps(req))

            raw_ack = await asyncio.wait_for(ws.recv(), timeout=2.0)
            self.assertEqual(json.loads(raw_ack).get("status"), "in_progress")

            raw_final = await asyncio.wait_for(ws.recv(), timeout=3.0)
            final_res = json.loads(raw_final)
            self.assertFalse(final_res.get("success"))
            self.assertEqual(final_res.get("id"), "busy-test-3")
            self.assertEqual(final_res["data"]["mode"], "cdp_cast_busy_other_app")
            self.assertEqual(final_res["data"]["cast_stream"]["display_name"], "Netflix")

    @patch("bingo.actions.music.play_playlist")
    async def test_concurrent_music_rejection(self, mock_play):
        """Valida que solicitações concorrentes são rejeitadas com status busy / already_in_progress."""
        import time

        def slow_play(*args, **kwargs):
            time.sleep(0.5)
            return {
                "success": True,
                "mode": "cdp_cast_confirmed",
                "message": "Sucesso",
                "cast_stream": {"confirmed": True},
            }

        mock_play.side_effect = slow_play

        async with websockets.connect(self.uri) as ws:
            # Envia a primeira requisição que ocupará o lock
            await ws.send(json.dumps({"type": "command", "command": "play_music", "id": "req-1"}))
            ack1 = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
            self.assertEqual(ack1.get("status"), "in_progress")

            # Imediatamente envia uma segunda requisição enquanto a primeira ainda executa
            await ws.send(json.dumps({"type": "command", "command": "play_music", "id": "req-2"}))
            res2 = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))

            # A segunda requisição deve ser rejeitada imediatamente com status busy
            self.assertFalse(res2.get("success"))
            self.assertEqual(res2.get("status"), "busy")
            self.assertEqual(res2.get("id"), "req-2")
            self.assertEqual(res2["data"]["mode"], "already_in_progress")

            # Aguarda a finalização da primeira requisição
            final_res1 = json.loads(await asyncio.wait_for(ws.recv(), timeout=3.0))
            self.assertTrue(final_res1.get("success"))
            self.assertEqual(final_res1.get("id"), "req-1")

    @patch("bingo.actions.music.play_playlist")
    async def test_play_music_internal_error_handling(self, mock_play):
        """Valida tratamento seguro de erros inesperados sem travar o servidor."""
        mock_play.side_effect = RuntimeError("Erro de teste inesperado")

        async with websockets.connect(self.uri) as ws:
            await ws.send(json.dumps({"type": "command", "command": "play_music", "id": "err-1"}))
            ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.0))
            self.assertEqual(ack.get("status"), "in_progress")

            final_res = json.loads(await asyncio.wait_for(ws.recv(), timeout=3.0))
            self.assertFalse(final_res.get("success"))
            self.assertEqual(final_res.get("id"), "err-1")
            self.assertIn("Erro", final_res.get("message"))


if __name__ == "__main__":
    unittest.main()
