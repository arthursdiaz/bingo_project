package com.arthurdiaz.bingo.ui.components

import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.arthurdiaz.bingo.audio.VoiceState
import com.arthurdiaz.bingo.ui.theme.BingoDarkJungle
import com.arthurdiaz.bingo.ui.theme.BingoMagicMint

@Composable
fun BingoFaceCard(
    voiceState: VoiceState,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .aspectRatio(1.2f)
            .shadow(8.dp, RoundedCornerShape(24.dp))
            .clip(RoundedCornerShape(24.dp))
            .background(BingoMagicMint)
            .border(8.dp, BingoDarkJungle, RoundedCornerShape(24.dp))
            .padding(8.dp)
    ) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { context ->
                WebView(context).apply {
                    layoutParams = ViewGroup.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    )
                    webViewClient = WebViewClient()
                    settings.javaScriptEnabled = true
                    setBackgroundColor(0) // Transparent
                    loadUrl("file:///android_asset/rosto.html")
                }
            },
            update = { webView ->
                webView.evaluateJavascript("setVoiceState('${voiceState.name}')", null)
            }
        )
    }
}