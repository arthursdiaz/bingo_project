package com.arthurdiaz.bingo.audio

import android.util.Base64
import java.io.File

object Encoder {

    fun encode(
        file: File
    ): String {

        val bytes = file.readBytes()

        return Base64.encodeToString(
            bytes,
            Base64.NO_WRAP
        )

    }

}