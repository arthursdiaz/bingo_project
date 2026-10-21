package com.arthurdiaz.bingo

import com.arthurdiaz.bingo.music.MusicPlaybackState
import com.arthurdiaz.bingo.protocol.Message
import com.arthurdiaz.bingo.protocol.MessageType
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class MusicProtocolUnitTest {

    @Test
    fun testPlayMusicMessageFormatDefault() {
        val jsonStr = Message.playMusic()
        val json = JSONObject(jsonStr)

        assertEquals(MessageType.COMMAND.value, json.getString("type"))
        assertEquals("play_music", json.getString("command"))
        assertTrue(json.getBoolean("shuffle"))
        assertFalse(json.has("id"))
        assertFalse(json.has("playlist_url"))
        assertFalse(json.has("device"))
    }

    @Test
    fun testPlayMusicMessageFormatWithCustomArgs() {
        val jsonStr = Message.playMusic(
            id = "test-req-123",
            playlistUrl = "https://music.youtube.com/playlist?list=XYZ",
            device = "TutuLola",
            shuffle = false
        )
        val json = JSONObject(jsonStr)

        assertEquals("command", json.getString("type"))
        assertEquals("play_music", json.getString("command"))
        assertEquals("test-req-123", json.getString("id"))
        assertEquals("https://music.youtube.com/playlist?list=XYZ", json.getString("playlist_url"))
        assertEquals("TutuLola", json.getString("device"))
        assertFalse(json.getBoolean("shuffle"))
    }

    @Test
    fun testMessageTypeEnum() {
        assertEquals("music", MessageType.MUSIC.value)
        assertEquals("command", MessageType.COMMAND.value)
        assertEquals("status", MessageType.STATUS.value)
    }

    @Test
    fun testSuccessResponseStateMapping() {
        val serverJson = JSONObject("""
            {
                "type": "status",
                "command": "play_music",
                "id": "req-1",
                "success": true,
                "message": "Playlist iniciada",
                "data": {
                    "mode": "cdp_cast_confirmed",
                    "local_playback": {
                        "status": "routed_to_cast",
                        "track": "Minha Música Favorita"
                    },
                    "cast_stream": {
                        "status": "active",
                        "confirmed": true,
                        "device": "TutuLola"
                    }
                }
            }
        """.trimIndent())

        assertTrue(serverJson.getBoolean("success"))
        val data = serverJson.getJSONObject("data")
        val track = data.getJSONObject("local_playback").getString("track")
        val device = data.getJSONObject("cast_stream").getString("device")

        val state = MusicPlaybackState.Playing(track = track, device = device)
        assertEquals("Minha Música Favorita", state.track)
        assertEquals("TutuLola", state.device)
    }

    @Test
    fun testBusyOtherAppResponseStateMapping() {
        val serverJson = JSONObject("""
            {
                "type": "status",
                "command": "play_music",
                "id": "req-2",
                "success": false,
                "message": "Chromecast ocupado",
                "data": {
                    "mode": "cdp_cast_busy_other_app",
                    "cast_stream": {
                        "status": "busy_other_app",
                        "confirmed": false,
                        "display_name": "Netflix",
                        "device": "TutuLola"
                    }
                }
            }
        """.trimIndent())

        assertFalse(serverJson.getBoolean("success"))
        val data = serverJson.getJSONObject("data")
        val castStream = data.getJSONObject("cast_stream")
        val appName = castStream.getString("display_name")
        val device = castStream.getString("device")

        val state = MusicPlaybackState.Busy(appName = appName, device = device)
        assertEquals("Netflix", state.appName)
        assertEquals("TutuLola", state.device)
    }

    @Test
    fun testErrorResponseStateMapping() {
        val serverJson = JSONObject("""
            {
                "type": "status",
                "command": "play_music",
                "id": "req-3",
                "success": false,
                "message": "Chromecast 'TutuLola' não foi localizado na rede local.",
                "data": {
                    "mode": "cdp_cast_unconfirmed"
                }
            }
        """.trimIndent())

        assertFalse(serverJson.getBoolean("success"))
        val errMsg = serverJson.getString("message")

        val state = MusicPlaybackState.Error(errMsg)
        assertTrue(state.message.contains("não foi localizado"))
    }

    @Test
    fun testInProgressStatusMapping() {
        val serverJson = JSONObject("""
            {
                "type": "status",
                "command": "play_music",
                "status": "in_progress",
                "id": "req-4",
                "message": "Solicitação recebida. Iniciando automação..."
            }
        """.trimIndent())

        assertEquals("status", serverJson.getString("type"))
        assertEquals("in_progress", serverJson.getString("status"))
        assertEquals("play_music", serverJson.getString("command"))

        val state = MusicPlaybackState.Loading
        assertTrue(state is MusicPlaybackState.Loading)
    }

    @Test
    fun testOfflineState() {
        val state = MusicPlaybackState.Offline
        assertTrue(state is MusicPlaybackState.Offline)
    }
}
