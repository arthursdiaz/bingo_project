package com.arthurdiaz.bingo.protocol

enum class MessageType(
    val value: String
) {

    PING("ping"),
    PONG("pong"),

    COMMAND("command"),

    STATUS("status"),
    STATUS_INFO("status_info"),

    AUDIO("audio")
}