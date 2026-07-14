package com.arthurdiaz.bingo.network

import org.java_websocket.client.WebSocketClient
import org.java_websocket.handshake.ServerHandshake
import java.net.URI

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