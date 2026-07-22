package com.arthurdiaz.bingo.network

import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI
import org.json.JSONObject

class BingoSocket(
    serverUrl: String
) : WebSocketClient(URI(serverUrl)) {

    var onConnected: (() -> Unit)? = null

    var onDisconnected: (() -> Unit)? = null

    var onMessageReceived: ((String) -> Unit)? = null

    override fun onOpen(handshakedata: ServerHandshake?) {

        println("Connected!")

        onConnected?.invoke()
    }

    override fun onMessage(message: String?) {

        println("Received: $message")

        message?.let {

            try {
                val json = JSONObject(it)
                if (json.optString("type") == "ping") {
                    val pong = JSONObject().put("type", "pong").toString()
                    send(pong)
                    return
                }
            } catch (e: Exception) {
                // Ignore JSON parsing exceptions
            }

            onMessageReceived?.invoke(it)

        }
    }

    override fun onClose(
        code: Int,
        reason: String?,
        remote: Boolean
    ) {

        println("Disconnected")

        onDisconnected?.invoke()
    }

    override fun onError(ex: Exception?) {

        ex?.printStackTrace()

    }

    override fun send(
        message: String
    ) {

        super.send(message)

    }

}