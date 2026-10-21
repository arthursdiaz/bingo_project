package com.arthurdiaz.bingo.audio

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import com.arthurdiaz.bingo.audio.feedback.TonePlayer
import com.arthurdiaz.bingo.music.MusicPlaybackState
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import org.json.JSONObject
import java.io.File

class VoiceController(
    private val context: Context,
    private var serverUrl: String,
    private val recorder: Recorder,
    private val audioFile: File,
    private val onStateChanged: (VoiceState) -> Unit,
    private val onResponse: (String) -> Unit
) {

    private var speechRecognizer: SpeechRecognizer? = null
    private val handler = Handler(Looper.getMainLooper())
    private var currentState = VoiceState.DISCONNECTED
    
    private var currentSocket: BingoSocket? = null
    private var reconnectAttempt = 0
    private val backoffMultipliers = listOf(1000L, 2000L, 5000L, 10000L)
    private var isManuallyClosed = false

    private val RECONNECT_TOKEN = Any()
    private val MUSIC_TIMEOUT_TOKEN = Any()
    private val VOICE_TOKEN = Any()

    var musicState: MusicPlaybackState = MusicPlaybackState.Idle
        private set
    var onMusicStateChanged: ((MusicPlaybackState) -> Unit)? = null
    private var pendingMusicRequestId: String? = null

    init {
        setupSpeechRecognizer()
    }

    fun isConnected(): Boolean {
        return currentSocket?.isOpen == true
    }

    fun getServerUrl(): String = serverUrl

    fun updateServerUrl(newUrl: String) {
        serverUrl = newUrl
        connect(isAutomatic = false)
    }

    fun connect(isAutomatic: Boolean = false) {
        Log.d("VoiceController", "Connecting to $serverUrl (auto=$isAutomatic)")
        isManuallyClosed = false
        handler.removeCallbacksAndMessages(RECONNECT_TOKEN)
        
        if (!isAutomatic) {
            reconnectAttempt = 0
        }

        val isReconnection = reconnectAttempt > 0
        
        currentState = VoiceState.CONNECTING
        onStateChanged(VoiceState.CONNECTING)
        
        if (isReconnection) {
            TonePlayer.playReconnecting()
        }
        
        createNewSocket(isReconnection)
    }

    private fun updateMusicState(newState: MusicPlaybackState) {
        musicState = newState
        onMusicStateChanged?.invoke(newState)
    }

    fun playMusic(
        playlistUrl: String? = null,
        device: String? = null,
        shuffle: Boolean = true
    ): Boolean {
        if (!isConnected()) {
            TonePlayer.playError()
            updateMusicState(MusicPlaybackState.Offline)
            handler.postDelayed({
                if (musicState is MusicPlaybackState.Offline) {
                    updateMusicState(MusicPlaybackState.Idle)
                }
            }, 3000)
            return false
        }

        if (musicState is MusicPlaybackState.Loading) {
            // Previne cliques múltiplos enquanto uma operação está em andamento
            Log.w("VoiceController", "Música já está sendo carregada, ignorando clique repetido")
            return false
        }

        val reqId = "music_${System.currentTimeMillis()}"
        pendingMusicRequestId = reqId
        updateMusicState(MusicPlaybackState.Loading)

        val message = Message.playMusic(
            id = reqId,
            playlistUrl = playlistUrl,
            device = device,
            shuffle = shuffle
        )
        send(message)

        // Safety timeout de 45 segundos para restaurar o estado caso o núcleo não responda
        handler.removeCallbacksAndMessages(MUSIC_TIMEOUT_TOKEN)
        handler.postAtTime({
            if (musicState is MusicPlaybackState.Loading) {
                TonePlayer.playError()
                updateMusicState(MusicPlaybackState.Error("Tempo limite excedido ao aguardar o Chromecast"))
                handler.postDelayed({
                    if (musicState is MusicPlaybackState.Error) {
                        updateMusicState(MusicPlaybackState.Idle)
                    }
                }, 5000)
            }
        }, MUSIC_TIMEOUT_TOKEN, SystemClock.uptimeMillis() + 45000L)

        return true
    }

    private fun handleStatusMessage(message: String) {
        try {
            val json = JSONObject(message)
            val type = json.optString("type")
            if (type != "status") return

            val command = json.optString("command")
            val msgId = json.optString("id")
            val data = json.optJSONObject("data")
            val isMusicMsg = command == "play_music" || 
                (pendingMusicRequestId != null && msgId == pendingMusicRequestId) ||
                data?.has("cast_stream") == true

            if (!isMusicMsg) return

            val status = json.optString("status")
            if (status == "in_progress") {
                // Solicitação aceita e execução em andamento no núcleo
                updateMusicState(MusicPlaybackState.Loading)
                return
            }

            handler.removeCallbacksAndMessages(MUSIC_TIMEOUT_TOKEN)

            val isSuccess = json.optBoolean("success", false)
            if (isSuccess) {
                val castStream = data?.optJSONObject("cast_stream")
                val localPlayback = data?.optJSONObject("local_playback")
                val rawTrack = localPlayback?.optString("track")
                val track = if (!rawTrack.isNullOrBlank() && rawTrack != "Desconhecido") rawTrack else null
                val targetDevice = castStream?.optString("device")?.takeIf { it.isNotBlank() } ?: "TutuLola"
                
                TonePlayer.playSuccess()
                updateMusicState(MusicPlaybackState.Playing(track = track, device = targetDevice))
            } else {
                TonePlayer.playError()
                val mode = data?.optString("mode")
                val castStream = data?.optJSONObject("cast_stream")
                val castStatus = castStream?.optString("status")
                val isBusy = mode == "cdp_cast_busy_other_app" || castStatus == "busy_other_app"

                if (isBusy) {
                    val appName = castStream?.optString("display_name") ?: "Outro App"
                    val dev = castStream?.optString("device") ?: "TutuLola"
                    updateMusicState(MusicPlaybackState.Busy(appName = appName, device = dev))
                } else {
                    val errMsg = json.optString("message").ifEmpty { "Falha na transmissão para o Chromecast" }
                    updateMusicState(MusicPlaybackState.Error(errMsg))
                }

                // Restaura para Idle após 5 segundos para permitir nova tentativa
                handler.postDelayed({
                    if (musicState !is MusicPlaybackState.Playing) {
                        updateMusicState(MusicPlaybackState.Idle)
                    }
                }, 5000)
            }
        } catch (e: Exception) {
            Log.e("VoiceController", "Erro ao processar mensagem de status musical", e)
        }
    }

    private fun createNewSocket(isReconnection: Boolean) {
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
                
                currentState = VoiceState.IDLE
                onStateChanged(VoiceState.IDLE)
                reconnectAttempt = 0
                
                TonePlayer.playConnected()
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

                    handler.removeCallbacksAndMessages(MUSIC_TIMEOUT_TOKEN)
                    if (musicState is MusicPlaybackState.Loading || musicState is MusicPlaybackState.Playing) {
                        updateMusicState(MusicPlaybackState.Offline)
                        handler.postDelayed({
                            if (musicState is MusicPlaybackState.Offline) {
                                updateMusicState(MusicPlaybackState.Idle)
                            }
                        }, 4000)
                    }

                    scheduleReconnection()
                }
            }
        }

        newSocket.onMessageReceived = { message ->
            handler.post {
                if (currentSocket != newSocket) return@post
                onResponse(message)
                handleStatusMessage(message)
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
                connect(isAutomatic = true)
            }
        }, RECONNECT_TOKEN, SystemClock.uptimeMillis() + delay)
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
        handler.postAtTime({
            stopAndProcess()
        }, VOICE_TOKEN, SystemClock.uptimeMillis() + 5000L)
    }

    private fun stopAndProcess() {
        if (currentState != VoiceState.LISTENING) return

        currentState = VoiceState.PROCESSING
        onStateChanged(VoiceState.PROCESSING)

        recorder.stop()

        val base64 = Encoder.encode(audioFile)
        send(Message.audio("audio.m4a", base64))
        
        handler.postAtTime({
            if (currentState == VoiceState.PROCESSING) {
                resetToIdle()
            }
        }, VOICE_TOKEN, SystemClock.uptimeMillis() + 12000L)
    }

    fun onResponseReceived() {
        if (currentState == VoiceState.PROCESSING) {
            TonePlayer.playSuccess()
            resetToIdle()
        }
    }

    fun onError() {
        currentState = VoiceState.ERROR
        onStateChanged(VoiceState.ERROR)
        TonePlayer.playError()
        handler.postAtTime({
            resetToIdle()
        }, VOICE_TOKEN, SystemClock.uptimeMillis() + 3000L)
    }

    fun resetToIdle() {
        handler.removeCallbacksAndMessages(VOICE_TOKEN)
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
        currentSocket?.let {
            it.onConnected = null
            it.onDisconnected = null
            it.onMessageReceived = null
            if (it.isOpen) it.close()
        }
    }
}