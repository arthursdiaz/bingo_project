package com.arthurdiaz.bingo

import androidx.compose.foundation.layout.*
import androidx.compose.material3.Button
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.material3.BasicAlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.ui.window.DialogProperties

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import com.arthurdiaz.bingo.ui.theme.BingoAndroidTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()
        setContent {
            BingoAndroidTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    BingoScreen(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BingoScreen(
    modifier: Modifier = Modifier
) {

    var connected by remember {
        mutableStateOf(false)
    }

    var response by remember {
        mutableStateOf("-")
    }

    var showRosto by remember {
        mutableStateOf(false)
    }

    val socket = remember {
        BingoSocket("ws://192.168.0.18:8765")
    }

    if (showRosto) {
        BasicAlertDialog(
            onDismissRequest = { showRosto = false },
            properties = DialogProperties(usePlatformDefaultWidth = false)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
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
                            loadUrl("file:///android_asset/rosto.html")
                        }
                    }
                )
            }
        }
    }

    LaunchedEffect(Unit) {
    
        socket.onConnected = {
    
            connected = true
    
        }
    
        socket.onDisconnected = {
    
            connected = false
    
        }
    
        socket.onMessageReceived = {
    
            response = it
    
        }
    
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),

        horizontalAlignment = Alignment.CenterHorizontally,

        verticalArrangement = Arrangement.Center

    ) {

        Text("🤖 Bingo")

        Spacer(
            modifier = Modifier.height(32.dp)
        )

        Text(
            if (connected)
                "🟢 Connected"
            else
                "🔴 Disconnected"
        )

        Spacer(
            modifier = Modifier.height(24.dp)
        )

        Button(
        
            onClick = {
        
                socket.connect()
        
            }
        
        ) {
        
            Text("Conectar")
        
        }

        Spacer(
            modifier = Modifier.height(16.dp)
        )

        Button(
        
            onClick = {
        
                socket.send(
                    Message.ping()
                )
        
            }
        
        ) {
        
            Text("Ping")
        
        }

        Spacer(
            modifier = Modifier.height(16.dp)
        )

        Button(
            onClick = {
                showRosto = true
            }
        ) {
            Text("Abrir Rosto")
        }

        Text("Programas")

        Spacer(
            modifier = Modifier.height(16.dp)
        )
        
        Button(
        
            onClick = {
        
                socket.send(
        
                    Message.openProgram(
                        "system_settings"
                    )
        
                )
        
            }
        
        ) {
        
            Text("Configurações")
        
        }

        Spacer(
            modifier = Modifier.height(8.dp)
        )

        Button(
        
            onClick = {
        
                socket.send(
        
                    Message.openProgram(
                        "vivaldi"
                    )
        
                )
        
            }
        
        ) {
        
            Text("Vivaldi")
        
        }

        Spacer(
            modifier = Modifier.height(8.dp)
        )

        Button(
        
            onClick = {
        
                socket.send(
        
                    Message.openProgram(
                        "konsole"
                    )
        
                )
        
            }
        
        ) {
        
            Text("Terminal")
        
        }

        Spacer(
            modifier = Modifier.height(24.dp)
        )

        Text(response)

    }

}