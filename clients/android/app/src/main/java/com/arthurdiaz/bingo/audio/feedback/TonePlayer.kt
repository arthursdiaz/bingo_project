package com.arthurdiaz.bingo.audio.feedback

import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Handler
import android.os.Looper

object TonePlayer {
    private val toneGenerator = ToneGenerator(AudioManager.STREAM_MUSIC, 100)
    private val handler = Handler(Looper.getMainLooper())

    /**
     * Cute robot "Wake up" chirp (High pitched, fast)
     */
    fun playListening() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_DTMF_D, 60)
            handler.postDelayed({
                toneGenerator.startTone(ToneGenerator.TONE_DTMF_A, 60)
            }, 70)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Happy robot "Success" melody (Ascending and bright)
     */
    fun playSuccess() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_DTMF_C, 80)
            handler.postDelayed({
                toneGenerator.startTone(ToneGenerator.TONE_DTMF_7, 80)
            }, 100)
            handler.postDelayed({
                toneGenerator.startTone(ToneGenerator.TONE_DTMF_3, 120)
            }, 200)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    /**
     * Soft, mild robot "Not understood" (Gentle drop)
     */
    fun playError() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_CDMA_SOFT_ERROR_LITE, 200)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun playConnected() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP, 80)
            handler.postDelayed({
                toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP, 80)
            }, 120)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun playDisconnected() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP2, 200)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun playReconnecting() {
        try {
            toneGenerator.startTone(ToneGenerator.TONE_PROP_BEEP, 100)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}