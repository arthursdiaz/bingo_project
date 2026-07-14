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
        target: String
    ): String {

        return JSONObject()

            .put("type", MessageType.COMMAND.value)
            .put("command", "open_program")
            .put("target", target)

            .toString()

    }

    fun audio(
        filename: String,
        data: String
    ): String {

        return JSONObject()

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

            .toString()

    }

}