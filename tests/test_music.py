import unittest
from unittest.mock import patch, MagicMock

from bingo.actions.music import (
    build_ytm_url,
    validate_prerequisites,
    verify_chromecast_playback,
    launch_vivaldi_with_cdp,
    restart_vivaldi_with_cdp,
    play_via_cdp,
    play_playlist,
    execute,
    DEFAULT_PLAYLIST_URL,
    DEFAULT_DEVICE_NAME,
)
from bingo.parser import parse
from bingo.protocol import MessageType
from bingo.dispatcher import Dispatcher
from bingo.state import state


class TestMusicAction(unittest.TestCase):

    def test_build_ytm_url_with_shuffle(self):
        url = "https://music.youtube.com/playlist?list=PL_SAMPLE_TEST_ID"
        expected = "https://music.youtube.com/watch?list=PL_SAMPLE_TEST_ID&shuffle=1"
        self.assertEqual(build_ytm_url(url, shuffle=True), expected)

    def test_build_ytm_url_without_shuffle(self):
        url = "https://music.youtube.com/playlist?list=PL_SAMPLE_TEST_ID"
        expected = "https://music.youtube.com/watch?list=PL_SAMPLE_TEST_ID"
        self.assertEqual(build_ytm_url(url, shuffle=False), expected)

    def test_build_ytm_url_preserves_unmatched(self):
        url = "https://music.youtube.com/watch?v=abc"
        self.assertEqual(build_ytm_url(url), url)

    def test_parser_music_phrases(self):
        phrases = [
            "toca musica",
            "tocar playlist",
            "tocar salgadinho",
            "tocar música no chromecast",
            "ouvir musica",
            "play playlist",
            "toque uma musica",
            "reproduzir playlist",
        ]
        for phrase in phrases:
            parsed = parse(phrase)
            self.assertIsNotNone(parsed, f"Falha ao interpretar frase: {phrase}")
            self.assertEqual(parsed.get("type"), MessageType.COMMAND.value)
            self.assertEqual(parsed.get("command"), "play_music")
            self.assertEqual(parsed.get("playlist_url"), DEFAULT_PLAYLIST_URL)
            self.assertTrue(parsed.get("shuffle"))

    def test_parser_preserves_existing_commands(self):
        parsed_open = parse("abre vivaldi")
        self.assertEqual(parsed_open.get("command"), "open_program")
        self.assertEqual(parsed_open.get("target"), "vivaldi")

        parsed_close = parse("fecha steam")
        self.assertEqual(parsed_close.get("command"), "close_program")
        self.assertEqual(parsed_close.get("target"), "steam")

    @patch("shutil.which", return_value="/usr/bin/vivaldi")
    @patch("bingo.actions.music.find_chromecast_device")
    @patch("bingo.actions.music.is_vivaldi_running", return_value=True)
    @patch("bingo.actions.music.is_cdp_available", return_value=False)
    def test_validate_prerequisites_success(self, mock_cdp, mock_running, mock_chromecast, mock_which):
        mock_chromecast.return_value = (
            {"name": "TutuLola", "host": "192.168.0.5", "port": 8009, "model": "Chromecast"},
            [{"name": "TutuLola", "host": "192.168.0.5", "port": 8009, "model": "Chromecast"}],
        )

        prereqs = validate_prerequisites(target_device="TutuLola")
        self.assertTrue(prereqs["ok"])
        self.assertTrue(prereqs["vivaldi_installed"])
        self.assertTrue(prereqs["vivaldi_running"])
        self.assertFalse(prereqs["cdp_available"])
        self.assertTrue(prereqs["chromecast_found"])
        self.assertEqual(len(prereqs["issues"]), 0)

    @patch("shutil.which", return_value="/usr/bin/vivaldi")
    @patch("bingo.actions.music.find_chromecast_device", return_value=(None, []))
    def test_validate_prerequisites_chromecast_missing(self, mock_chromecast, mock_which):
        prereqs = validate_prerequisites(target_device="Inexistente")
        self.assertFalse(prereqs["ok"])
        self.assertFalse(prereqs["chromecast_found"])
        self.assertTrue(any("não encontrado" in msg for msg in prereqs["issues"]))

    @patch("bingo.actions.music.validate_prerequisites")
    @patch("bingo.actions.music.open_in_vivaldi")
    @patch("bingo.actions.music.send_mpris_play")
    def test_play_playlist_success_native(self, mock_mpris, mock_open, mock_prereqs):
        mock_prereqs.return_value = {
            "ok": True,
            "vivaldi_installed": True,
            "vivaldi_running": True,
            "cdp_available": False,
            "chromecast_found": True,
            "target_device": {"name": "TutuLola", "host": "192.168.0.5", "port": 8009, "model": "Chromecast"},
            "issues": [],
        }

        result = play_playlist(
            playlist_url="https://music.youtube.com/playlist?list=PL_SAMPLE_TEST_ID",
            shuffle=True,
            device_name="TutuLola",
            skip_discovery=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["mode"], "native_instance_reused")
        self.assertIn("PL_SAMPLE_TEST_ID", result["url"])
        self.assertIn("shuffle=1", result["url"])
        mock_open.assert_called_once()
        self.assertIn("vivaldi", state.running_programs)
        self.assertEqual(state.last_command, "play_music")
        self.assertEqual(result["local_playback"]["status"], "playing")
        self.assertEqual(result["cast_stream"]["status"], "not_attempted_no_cdp")

    @patch("bingo.actions.music.validate_prerequisites")
    def test_play_playlist_chromecast_not_found(self, mock_prereqs):
        mock_prereqs.return_value = {
            "ok": False,
            "vivaldi_installed": True,
            "target_device": None,
            "issues": ["Chromecast não encontrado"],
        }

        result = play_playlist(
            playlist_url="https://music.youtube.com/playlist?list=PL_TEST",
            shuffle=True,
            device_name="TutuLola",
            skip_discovery=False,
        )

        self.assertFalse(result["success"])
        self.assertIn("não foi localizado", result["message"])

    @patch("bingo.actions.music.play_playlist")
    def test_execute_handler(self, mock_play):
        mock_play.return_value = {
            "success": True,
            "message": "Sucesso",
            "mode": "native_instance_reused",
        }

        msg = {
            "type": "command",
            "command": "play_music",
            "playlist_url": DEFAULT_PLAYLIST_URL,
        }
        resp = execute(msg)
        self.assertEqual(resp["type"], "status")
        self.assertTrue(resp["success"])
        self.assertEqual(resp["message"], "Sucesso")

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_confirmed_host(self, mock_get_cc):
        mock_cc = MagicMock()
        mock_cc.app_id = "2DB7CC49"
        mock_cc.status.display_name = "YouTube Music"
        mock_cc.status.is_stand_by = False
        mock_get_cc.return_value = mock_cc

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=1.0,
        )
        self.assertTrue(res["confirmed"])
        self.assertEqual(res["app_id"], "2DB7CC49")
        self.assertEqual(res["display_name"], "YouTube Music")

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_standby(self, mock_get_cc):
        mock_cc = MagicMock()
        mock_cc.app_id = "E8C28D3C"
        mock_cc.status.display_name = "Backdrop"
        mock_cc.status.is_stand_by = True
        mock_get_cc.return_value = mock_cc

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=1.0,
        )
        self.assertFalse(res["confirmed"])
        self.assertEqual(res["app_id"], "E8C28D3C")
        self.assertIn("permaneceu na tela de descanso", res["message"])

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_mirroring_rejected(self, mock_get_cc):
        mock_cc = MagicMock()
        mock_cc.app_id = "0F5096E8"
        mock_cc.status.display_name = "Chrome Mirroring"
        mock_cc.status.is_stand_by = False
        mock_get_cc.return_value = mock_cc

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=1.0,
            require_native=True,
        )
        self.assertFalse(res["confirmed"])
        self.assertTrue(res["is_mirroring"])
        self.assertEqual(res["app_id"], "0F5096E8")
        self.assertEqual(res["reason"], "mirroring_rejected")
        self.assertIn("Espelhamento de tela/aba detectado", res["message"])

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_session_dropped_immediately(self, mock_get_cc):
        # Primeiro mock: sessão ativa 2DB7CC49
        mock_cc_active = MagicMock()
        mock_cc_active.app_id = "2DB7CC49"
        mock_cc_active.status.display_name = "YouTube Music"
        mock_cc_active.status.is_stand_by = False

        # Segundo mock: sessão caiu para Backdrop E8C28D3C após intervalo de estabilidade
        mock_cc_dropped = MagicMock()
        mock_cc_dropped.app_id = "E8C28D3C"
        mock_cc_dropped.status.display_name = "Backdrop"
        mock_cc_dropped.status.is_stand_by = True

        mock_get_cc.side_effect = [mock_cc_active, mock_cc_dropped]

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=1.0,
            stability_interval=0.1,
            require_native=True,
        )
        self.assertFalse(res["confirmed"])
        self.assertEqual(res["reason"], "session_dropped_immediately")
        self.assertIn("encerrou imediatamente", res["message"])

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_connection_exception(self, mock_get_cc):
        mock_get_cc.side_effect = Exception("Conexão recusada na porta 8009")

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=0.2,
        )
        self.assertFalse(res["confirmed"])
        self.assertEqual(res["reason"], "standby_timeout")
        self.assertIn("permaneceu na tela de descanso", res["message"])

    @patch("pychromecast.get_chromecast_from_host")
    def test_verify_chromecast_playback_netflix_active_rejected(self, mock_get_cc):
        mock_cc = MagicMock()
        mock_cc.app_id = "CA5E8412"
        mock_cc.status.display_name = "Netflix"
        mock_cc.status.is_stand_by = False
        mock_get_cc.return_value = mock_cc

        res = verify_chromecast_playback(
            target_name="TutuLola",
            host="192.168.0.5",
            port=8009,
            timeout=1.0,
            require_native=True,
        )
        self.assertFalse(res["confirmed"])
        self.assertTrue(res["is_unrelated_app"])
        self.assertFalse(res["is_mirroring"])
        self.assertEqual(res["app_id"], "CA5E8412")
        self.assertEqual(res["reason"], "unrelated_app_busy")
        self.assertIn("Netflix", res["message"])
        self.assertIn("executando outro aplicativo", res["message"])

    @patch("bingo.actions.music._async_play_via_cdp")
    def test_play_via_cdp_wrapper(self, mock_async):
        mock_async.return_value = {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": "Playlist iniciada e confirmada",
            "local_playback": {"status": "routed_to_cast", "track": "Song - Artist"},
            "cast_stream": {"status": "active", "confirmed": True, "app_id": "2DB7CC49", "track": "Song - Artist"},
        }
        res = play_via_cdp("https://music.youtube.com/watch?list=abc", device_name="TutuLola")
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "cdp_cast_confirmed")
        self.assertTrue(res["cast_stream"]["confirmed"])

    @patch("bingo.actions.music._async_play_via_cdp")
    def test_play_via_cdp_netflix_busy_fails(self, mock_async):
        mock_async.return_value = {
            "success": False,
            "mode": "cdp_cast_busy_other_app",
            "message": "O Chromecast 'TutuLola' está ocupado executando outro aplicativo (Netflix [CA5E8412]).",
            "local_playback": {"status": "playing", "track": None},
            "cast_stream": {
                "status": "busy_other_app",
                "confirmed": False,
                "app_id": "CA5E8412",
                "display_name": "Netflix",
            },
        }
        res = play_via_cdp("https://music.youtube.com/watch?list=abc", device_name="TutuLola")
        self.assertFalse(res["success"])
        self.assertEqual(res["mode"], "cdp_cast_busy_other_app")
        self.assertFalse(res["cast_stream"]["confirmed"])
        self.assertEqual(res["cast_stream"]["app_id"], "CA5E8412")

    @patch("bingo.actions.music._async_play_via_cdp")
    def test_play_via_cdp_unknown_metadata_fails(self, mock_async):
        mock_async.return_value = {
            "success": False,
            "mode": "cdp_cast_unconfirmed_playback",
            "message": "O aplicativo YouTube Music [2DB7CC49] foi iniciado, mas os metadados da faixa não puderam ser confirmados.",
            "local_playback": {"status": "playing", "track": None},
            "cast_stream": {
                "status": "unconfirmed_playback",
                "confirmed": False,
                "app_id": "2DB7CC49",
                "display_name": "YouTube Music",
            },
        }
        res = play_via_cdp("https://music.youtube.com/watch?list=abc", device_name="TutuLola")
        self.assertFalse(res["success"])
        self.assertEqual(res["mode"], "cdp_cast_unconfirmed_playback")
        self.assertFalse(res["cast_stream"]["confirmed"])

    @patch("bingo.actions.music.validate_prerequisites")
    @patch("bingo.actions.music.play_via_cdp")
    def test_play_playlist_with_cdp_available(self, mock_cdp, mock_prereqs):
        mock_prereqs.return_value = {
            "ok": True,
            "vivaldi_installed": True,
            "vivaldi_running": True,
            "cdp_available": True,
            "chromecast_found": True,
            "target_device": {"name": "TutuLola", "host": "192.168.0.5", "port": 8009, "model": "Chromecast"},
            "issues": [],
        }
        mock_cdp.return_value = {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": "Transmissão confirmada",
            "local_playback": {"status": "playing"},
            "cast_stream": {"status": "active", "confirmed": True},
        }

        res = play_playlist(playlist_url="https://music.youtube.com/playlist?list=PL_TEST", device_name="TutuLola", skip_discovery=True)
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "cdp_cast_confirmed")
        mock_cdp.assert_called_once()

    @patch("bingo.actions.music.validate_prerequisites")
    @patch("bingo.actions.music.restart_vivaldi_with_cdp")
    @patch("bingo.actions.music.is_cdp_available", return_value=True)
    @patch("bingo.actions.music.is_vivaldi_running", return_value=True)
    @patch("bingo.actions.music.play_via_cdp")
    def test_play_playlist_with_restart_flag(self, mock_cdp, mock_running, mock_is_cdp, mock_restart, mock_prereqs):
        mock_prereqs.return_value = {
            "ok": True,
            "vivaldi_installed": True,
            "vivaldi_running": True,
            "cdp_available": False,
            "chromecast_found": True,
            "target_device": {"name": "TutuLola", "host": "192.168.0.5", "port": 8009, "model": "Chromecast"},
            "issues": [],
        }
        mock_cdp.return_value = {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": "Transmissão confirmada",
            "local_playback": {"status": "playing"},
            "cast_stream": {"status": "active", "confirmed": True},
        }

        res = play_playlist(
            playlist_url="https://music.youtube.com/playlist?list=PL_TEST",
            device_name="TutuLola",
            skip_discovery=True,
            restart_vivaldi=True,
        )
        mock_restart.assert_called_once()
        self.assertTrue(res["success"])
        self.assertEqual(res["mode"], "cdp_cast_confirmed")

    @patch("subprocess.Popen")
    @patch("bingo.actions.music.is_cdp_available", side_effect=[False, True])
    def test_launch_vivaldi_with_cdp(self, mock_cdp, mock_popen):
        res = launch_vivaldi_with_cdp()
        self.assertTrue(res)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertTrue(any("--remote-debugging-port=" in a for a in args))
        self.assertTrue(any("--remote-debugging-address=127.0.0.1" in a for a in args))

    @patch("subprocess.run")
    @patch("bingo.actions.music.is_vivaldi_running", side_effect=[True, False])
    @patch("bingo.actions.music.launch_vivaldi_with_cdp", return_value=True)
    def test_restart_vivaldi_with_cdp(self, mock_launch, mock_running, mock_run):
        res = restart_vivaldi_with_cdp()
        self.assertTrue(res)
        mock_run.assert_called()
        mock_launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
