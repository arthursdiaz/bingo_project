package com.arthurdiaz.bingo.audio.feedback

import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale

class SpeechFeedback(context: Context) {
    private var tts: TextToSpeech? = null
    private var isInitialized = false

    private val successPhrases = listOf("Ok.", "Pronto.", "Feito.", "Entendido.", "Certo.")
    private val connectedPhrases = listOf("Estou online.", "Conectado.", "Pronto.", "Olá.")
    private val reconnectPhrases = listOf("Estou de volta.", "Reconectado.")
    private val lostConnectionPhrases = listOf("Perdi a conexão.", "Tentando reconectar.")

    init {
        tts = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                tts?.language = Locale("pt", "BR")
                isInitialized = true
            }
        }
    }

    fun say(text: String) {
        if (isInitialized) {
            tts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, null)
        }
    }

    fun saySuccess() {
        say(successPhrases.random())
    }

    fun sayConnected() {
        say(connectedPhrases.random())
    }

    fun sayReconnected() {
        say(reconnectPhrases.random())
    }

    fun sayLostConnection() {
        say(lostConnectionPhrases.random())
    }

    fun sayError() {
        say("Houve um erro.")
    }

    fun shutdown() {
        tts?.stop()
        tts?.shutdown()
    }
}