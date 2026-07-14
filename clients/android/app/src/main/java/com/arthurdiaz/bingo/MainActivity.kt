package com.arthurdiaz.bingo

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.arthurdiaz.bingo.audio.Encoder
import com.arthurdiaz.bingo.audio.Recorder
import com.arthurdiaz.bingo.audio.VoiceController
import com.arthurdiaz.bingo.audio.VoiceState
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import com.arthurdiaz.bingo.ui.components.BmoFaceCard
import com.arthurdiaz.bingo.ui.components.BmoMenu
import com.arthurdiaz.bingo.ui.theme.*
import java.io.File

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        
        // Hide system bars for immersive experience
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        windowInsetsController.hide(WindowInsetsCompat.Type.systemBars())

        setContent {
            BingoAndroidTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = BmoTeal
                ) {
                    BingoScreen()
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BingoScreen() {
    val context = LocalContext.current
    var connected by remember { mutableStateOf(false) }
    var response by remember { mutableStateOf("-") }
    var voiceState by remember { mutableStateOf(VoiceState.SLEEPING) }
    var recording by remember { mutableStateOf(false) }

    val socket = remember { BingoSocket("ws://192.168.0.18:8765") }
    val audioFile = remember { File(context.cacheDir, "audio.m4a") }
    val recorder = remember { Recorder(audioFile) }
    val voiceController = remember {
        VoiceController(
            context = context,
            socket = socket,
            recorder = recorder,
            audioFile = audioFile,
            onStateChanged = { newState -> voiceState = newState }
        )
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* Permission handle */ }

    LaunchedEffect(Unit) {
        socket.onConnected = {
            connected = true
            voiceState = VoiceState.IDLE
            val permissionCheckResult = ContextCompat.checkSelfPermission(
                context, Manifest.permission.RECORD_AUDIO
            )
            if (permissionCheckResult == PackageManager.PERMISSION_GRANTED) {
                voiceController.startHotwordDetection()
            }
        }
        socket.onDisconnected = {
            connected = false
            voiceState = VoiceState.SLEEPING
        }
        socket.onMessageReceived = {
            response = it
            voiceController.resetToIdle()
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp)
                .padding(top = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header / Logo
            Text(
                text = "BINGO",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = BmoDarkJungle,
                letterSpacing = 4.sp
            )
            Text(
                text = "BINGO OS v1.0",
                fontSize = 12.sp,
                color = BmoDarkJungle.copy(alpha = 0.7f)
            )

            Spacer(modifier = Modifier.height(48.dp))

            // Main Face Area
            BmoFaceCard(
                voiceState = voiceState,
                modifier = Modifier.weight(1f)
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Status Indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .background(BmoDarkJungle, RoundedCornerShape(16.dp))
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .background(
                            if (connected) Color.Green else Color.Red,
                            CircleShape
                        )
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = if (connected) "ONLINE" else "OFFLINE",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Main Connect Button
            Button(
                onClick = { if (!connected) socket.connect() },
                modifier = Modifier
                    .fillMaxWidth(0.7f)
                    .height(56.dp),
                shape = RoundedCornerShape(28.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = BmoActionRed,
                    contentColor = Color.White
                ),
                elevation = ButtonDefaults.buttonElevation(defaultElevation = 6.dp)
            ) {
                Text(
                    text = if (connected) "RECONECTAR" else "CONECTAR",
                    fontWeight = FontWeight.Bold,
                    fontSize = 16.sp
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Server Response Text
            Surface(
                modifier = Modifier.fillMaxWidth().height(60.dp),
                color = BmoDarkJungle.copy(alpha = 0.1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = response,
                        color = BmoDarkJungle,
                        fontSize = 14.sp,
                        maxLines = 2
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(80.dp)) // Space for FAB
        }

        // The Hidden Menu
        BmoMenu(
            isRecording = recording,
            onManualRecord = {
                val permissionCheckResult = ContextCompat.checkSelfPermission(
                    context, Manifest.permission.RECORD_AUDIO
                )
                if (permissionCheckResult == PackageManager.PERMISSION_GRANTED) {
                    recorder.start()
                    recording = true
                } else {
                    permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                }
            },
            onStopRecord = {
                recorder.stop()
                val base64 = Encoder.encode(audioFile)
                socket.send(Message.audio("audio.m4a", base64))
                recording = false
            },
            onOpenProgram = { target ->
                socket.send(Message.openProgram(target))
            }
        )
    }
}