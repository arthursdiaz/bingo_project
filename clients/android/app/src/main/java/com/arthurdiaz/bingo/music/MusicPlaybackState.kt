package com.arthurdiaz.bingo.music

sealed class MusicPlaybackState {
    object Idle : MusicPlaybackState()
    object Loading : MusicPlaybackState()
    data class Playing(val track: String?, val device: String) : MusicPlaybackState()
    data class Busy(val appName: String, val device: String) : MusicPlaybackState()
    data class Error(val message: String) : MusicPlaybackState()
    object Offline : MusicPlaybackState()
}
