package com.arthurdiaz.bingo.protocol

import org.json.JSONObject

object Message {

    fun ping(): String {

        return JSONObject()

            .put("type", MessageType.PING.value)

            .toString()

    }

    fun status(): String {

        return JSONObject()

            .put("type", MessageType.STATUS.value)

            .toString()

    }

    fun openProgram(
        target: String,
        id: String? = null
    ): String {

        val json = JSONObject()
            .put("type", MessageType.COMMAND.value)
            .put("command", "open_program")
            .put("target", target)

        if (id != null) {
            json.put("id", id)
        }

        return json.toString()

    }

    fun playMusic(
        id: String? = null,
        playlistUrl: String? = null,
        device: String? = null,
        shuffle: Boolean = true
    ): String {

        val json = JSONObject()
            .put("type", MessageType.COMMAND.value)
            .put("command", "play_music")
            .put("shuffle", shuffle)

        if (id != null) {
            json.put("id", id)
        }
        if (playlistUrl != null) {
            json.put("playlist_url", playlistUrl)
        }
        if (device != null) {
            json.put("device", device)
        }

        return json.toString()

    }

    fun audio(
        filename: String,
        data: String,
        id: String? = null
    ): String {

        val json = JSONObject()
            .put(
                "type",
                MessageType.AUDIO.value
            )
            .put(
                "filename",
                filename
            )
            .put(
                "data",
                data
            )

        if (id != null) {
            json.put("id", id)
        }

        return json.toString()

    }

}