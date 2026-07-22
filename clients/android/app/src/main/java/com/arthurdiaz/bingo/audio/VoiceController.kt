package com.arthurdiaz.bingo.audio

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import com.arthurdiaz.bingo.audio.feedback.SpeechFeedback
import com.arthurdiaz.bingo.audio.feedback.TonePlayer
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import java.io.File

class VoiceController(
    private val context: Context,
    private val serverUrl: String,
    private val recorder: Recorder,
    private val audioFile: File,
    private val onStateChanged: (VoiceState) -> Unit,
    private val onResponse: (String) -> Unit
) {

    private var speechRecognizer: SpeechRecognizer? = null
    private val handler = Handler(Looper.getMainLooper())
    private var currentState = VoiceState.DISCONNECTED
    private val speechFeedback = SpeechFeedback(context)
    
    private var currentSocket: BingoSocket? = null
    private var reconnectAttempt = 0
    private val backoffMultipliers = listOf(1000L, 2000L, 5000L, 10000L)
    private var isManuallyClosed = false

    private val RECONNECT_TOKEN = Any()

    init {
        setupSpeechRecognizer()
    }

    fun connect() {
        Log.d("VoiceController", "Connecting to $serverUrl")
        isManuallyClosed = false
        handler.removeCallbacksAndMessages(RECONNECT_TOKEN)
        
        currentState = VoiceState.CONNECTING
        onStateChanged(VoiceState.CONNECTING)
        TonePlayer.playReconnecting()
        
        createNewSocket()
    }

    private fun createNewSocket() {
        // 1. Clean up old socket
        currentSocket?.let { oldSocket ->
            oldSocket.onConnected = null
            oldSocket.onDisconnected = null
            oldSocket.onMessageReceived = null
            try {
                oldSocket.close()
            } catch (e: Exception) {
                Log.e("VoiceController", "Error closing old socket", e)
            }
        }

        // 2. Create new instance
        val newSocket = BingoSocket(serverUrl)
        
        newSocket.onConnected = {
            handler.post {
                if (currentSocket != newSocket) return@post
                
                val wasReconnecting = currentState == VoiceState.CONNECTING
                currentState = VoiceState.IDLE
                onStateChanged(VoiceState.IDLE)
                reconnectAttempt = 0
                
                TonePlayer.playConnected()
                if (wasReconnecting) {
                    speechFeedback.sayReconnected()
                } else {
                    speechFeedback.sayConnected()
                }
                
                startHotwordDetection()
            }
        }

        newSocket.onDisconnected = {
            handler.post {
                if (currentSocket != newSocket) return@post
                if (!isManuallyClosed) {
                    currentState = VoiceState.DISCONNECTED
                    onStateChanged(VoiceState.DISCONNECTED)
                    TonePlayer.playDisconnected()
                    speechFeedback.sayLostConnection()
                    scheduleReconnection()
                }
            }
        }

        newSocket.onMessageReceived = { message ->
            handler.post {
                if (currentSocket != newSocket) return@post
                onResponse(message)
                onResponseReceived()
            }
        }

        currentSocket = newSocket

        // 3. Connect
        try {
            newSocket.connect()
        } catch (e: Exception) {
            Log.e("VoiceController", "Error starting socket connection", e)
            handler.post {
                currentState = VoiceState.DISCONNECTED
                onStateChanged(VoiceState.DISCONNECTED)
                scheduleReconnection()
            }
        }
    }

    private fun scheduleReconnection() {
        if (isManuallyClosed) return
        
        handler.removeCallbacksAndMessages(RECONNECT_TOKEN)
        
        val delay = backoffMultipliers.getOrElse(reconnectAttempt) { backoffMultipliers.last() }
        reconnectAttempt++
        
        Log.d("VoiceController", "Scheduling reconnection in ${delay}ms (attempt $reconnectAttempt)")
        
        handler.postAtTime({
            if (currentState == VoiceState.DISCONNECTED) {
                connect()
            }
        }, RECONNECT_TOKEN, android.os.SystemClock.uptimeMillis() + delay)
    }

    fun send(message: String) {
        try {
            currentSocket?.let {
                if (it.isOpen) {
                    it.send(message)
                } else {
                    Log.w("VoiceController", "Socket is not open, cannot send message")
                }
            }
        } catch (e: Exception) {
            Log.e("VoiceController", "Error sending message", e)
        }
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
        if (currentState != VoiceState.IDLE) return
        
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
        send(Message.audio("audio.m4a", base64))
        
        handler.postDelayed({
            if (currentState == VoiceState.PROCESSING) {
                resetToIdle()
            }
        }, 12000) 
    }

    fun onResponseReceived() {
        if (currentState == VoiceState.PROCESSING) {
            TonePlayer.playSuccess()
            speechFeedback.saySuccess()
            resetToIdle()
        }
    }

    fun onError() {
        currentState = VoiceState.ERROR
        onStateChanged(VoiceState.ERROR)
        TonePlayer.playError()
        speechFeedback.sayError()
        handler.postDelayed({
            resetToIdle()
        }, 3000)
    }

    fun resetToIdle() {
        handler.removeCallbacksAndMessages(null)
        if (currentSocket?.isOpen == true) {
            currentState = VoiceState.IDLE
            onStateChanged(VoiceState.IDLE)
            startHotwordDetection()
        } else {
            currentState = VoiceState.DISCONNECTED
            onStateChanged(VoiceState.DISCONNECTED)
            scheduleReconnection()
        }
    }

    fun destroy() {
        isManuallyClosed = true
        handler.removeCallbacksAndMessages(null)
        speechRecognizer?.destroy()
        speechFeedback.shutdown()
        currentSocket?.let {
            it.onConnected = null
            it.onDisconnected = null
            it.onMessageReceived = null
            if (it.isOpen) it.close()
        }
    }
}