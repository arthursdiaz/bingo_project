package com.arthurdiaz.bingo.audio

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.arthurdiaz.bingo.audio.feedback.TonePlayer
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import java.io.File

class VoiceController(
    private val context: Context,
    private val socket: BingoSocket,
    private val recorder: Recorder,
    private val audioFile: File,
    private val onStateChanged: (VoiceState) -> Unit
) {

    private var speechRecognizer: SpeechRecognizer? = null
    private val handler = Handler(Looper.getMainLooper())
    private var currentState = VoiceState.IDLE

    init {
        setupSpeechRecognizer()
    }

    private fun setupSpeechRecognizer() {
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(object : RecognitionListener {
                override fun onReadyForSpeech(params: Bundle?) {}
                override fun onBeginningOfSpeech() {}
                override fun onRmsChanged(rmsdB: Float) {}
                override fun onBufferReceived(buffer: ByteArray?) {}
                override fun onEndOfSpeech() {}
                override fun onError(error: Int) {
                    if (currentState == VoiceState.IDLE) {
                        startHotwordDetection()
                    }
                }

                override fun onResults(results: Bundle?) {
                    val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val isHotword = matches?.any { it.contains("bingo", ignoreCase = true) } == true

                    if (isHotword && currentState == VoiceState.IDLE) {
                        startListeningFlow()
                    } else if (currentState == VoiceState.IDLE) {
                        startHotwordDetection()
                    }
                }

                override fun onPartialResults(partialResults: Bundle?) {
                    val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    val isHotword = matches?.any { it.contains("bingo", ignoreCase = true) } == true
                    if (isHotword && currentState == VoiceState.IDLE) {
                        startListeningFlow()
                    }
                }
                override fun onEvent(eventType: Int, params: Bundle?) {}
            })
        }
    }

    fun startHotwordDetection() {
        handler.post {
            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR")
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            }
            speechRecognizer?.startListening(intent)
        }
    }

    private fun startListeningFlow() {
        currentState = VoiceState.LISTENING
        onStateChanged(VoiceState.LISTENING)
        
        TonePlayer.playListening()

        recorder.start()

        // Record for 5 seconds
        handler.postDelayed({
            stopAndProcess()
        }, 5000)
    }

    private fun stopAndProcess() {
        if (currentState != VoiceState.LISTENING) return

        currentState = VoiceState.PROCESSING
        onStateChanged(VoiceState.PROCESSING)

        recorder.stop()

        val base64 = Encoder.encode(audioFile)
        socket.send(Message.audio("audio.m4a", base64))
        
        handler.postDelayed({
            if (currentState == VoiceState.PROCESSING) {
                resetToIdle()
            }
        }, 12000) 
    }

    fun onResponseReceived() {
        if (currentState == VoiceState.PROCESSING) {
            TonePlayer.playSuccess()
            resetToIdle()
        }
    }

    fun onError() {
        TonePlayer.playError()
        resetToIdle()
    }

    fun resetToIdle() {
        handler.removeCallbacksAndMessages(null)
        currentState = VoiceState.IDLE
        onStateChanged(VoiceState.IDLE)
        startHotwordDetection()
    }

    fun destroy() {
        speechRecognizer?.destroy()
    }
}