package com.arthurdiaz.bingo.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
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
import com.arthurdiaz.bingo.audio.Recorder
import com.arthurdiaz.bingo.audio.VoiceController
import com.arthurdiaz.bingo.audio.VoiceState
import com.arthurdiaz.bingo.network.BingoSocket
import com.arthurdiaz.bingo.protocol.Message
import com.arthurdiaz.bingo.ui.components.BingoFaceCard
import com.arthurdiaz.bingo.ui.components.BingoMenu
import com.arthurdiaz.bingo.ui.theme.*
import java.io.File

@Composable
fun BingoScreen() {
    val context = LocalContext.current
    var connected by remember { mutableStateOf(false) }
    var response by remember { mutableStateOf("-") }
    var voiceState by remember { mutableStateOf(VoiceState.SLEEPING) }

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
            } else {
                permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
        socket.onDisconnected = {
            connected = false
            voiceState = VoiceState.SLEEPING
        }
        socket.onMessageReceived = {
            response = it
            voiceController.onResponseReceived()
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
                color = BingoDarkJungle,
                letterSpacing = 4.sp
            )
            Text(
                text = "BINGO OS v1.0",
                fontSize = 12.sp,
                color = BingoDarkJungle.copy(alpha = 0.7f)
            )

            Spacer(modifier = Modifier.height(48.dp))

            // Main Face Area
            BingoFaceCard(
                voiceState = voiceState,
                modifier = Modifier.weight(1f)
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Status Indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .background(BingoDarkJungle, RoundedCornerShape(16.dp))
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
                shape = RoundedCornerShape(16.dp), // Retro square shape
                colors = ButtonDefaults.buttonColors(
                    containerColor = BingoActionRed,
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
                color = BingoDarkJungle.copy(alpha = 0.1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = response,
                        color = BingoDarkJungle,
                        fontSize = 14.sp,
                        maxLines = 2
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(80.dp)) // Space for FAB
        }

        // The Hidden Menu
        BingoMenu(
            onOpenProgram = { target ->
                socket.send(Message.openProgram(target))
            }
        )
    }
}