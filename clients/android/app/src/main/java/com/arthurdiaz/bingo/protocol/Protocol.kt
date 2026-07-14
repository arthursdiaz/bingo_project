package com.arthurdiaz.bingo.protocol

import org.json.JSONObject

object Protocol {

    fun type(
        message: String
    ): String {

        return JSONObject(message)

            .getString("type")

    }

}