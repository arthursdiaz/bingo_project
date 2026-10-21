package com.arthurdiaz.bingo.ui.screens

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.arthurdiaz.bingo.audio.Recorder
import com.arthurdiaz.bingo.audio.VoiceController
import com.arthurdiaz.bingo.audio.VoiceState
import com.arthurdiaz.bingo.music.MusicPlaybackState
import com.arthurdiaz.bingo.protocol.Message
import com.arthurdiaz.bingo.ui.components.BingoFaceCard
import com.arthurdiaz.bingo.ui.components.BingoMenu
import com.arthurdiaz.bingo.ui.theme.*
import org.json.JSONObject
import java.io.File

@Composable
fun BingoScreen() {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("bingo_prefs", Context.MODE_PRIVATE) }
    var serverUrl by remember {
        mutableStateOf(prefs.getString("server_url", "ws://192.168.0.27:8765") ?: "ws://192.168.0.27:8765")
    }
    var showServerConfigDialog by remember { mutableStateOf(false) }

    var response by remember { mutableStateOf("-") }
    var voiceState by remember { mutableStateOf(VoiceState.DISCONNECTED) }
    var musicState by remember { mutableStateOf<MusicPlaybackState>(MusicPlaybackState.Idle) }

    val audioFile = remember { File(context.cacheDir, "audio.m4a") }
    val recorder = remember { Recorder(audioFile) }
    
    val voiceController = remember {
        VoiceController(
            context = context,
            serverUrl = serverUrl,
            recorder = recorder,
            audioFile = audioFile,
            onStateChanged = { newState -> voiceState = newState },
            onResponse = { msg ->
                val display = try {
                    val json = JSONObject(msg)
                    json.optString("message", msg)
                } catch (e: Exception) {
                    msg
                }
                response = display
            }
        )
    }

    // Auto‑connect to the Bingo server when the screen appears
    LaunchedEffect(Unit) {
        voiceController.connect()
    }

    LaunchedEffect(voiceController) {
        voiceController.onMusicStateChanged = { newState ->
            musicState = newState
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            voiceController.destroy()
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            voiceController.startHotwordDetection()
        }
    }

    LaunchedEffect(Unit) {
        // Check for record permission on start
        val permissionCheckResult = ContextCompat.checkSelfPermission(
            context, Manifest.permission.RECORD_AUDIO
        )
        if (permissionCheckResult != PackageManager.PERMISSION_GRANTED) {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
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

            Spacer(modifier = Modifier.height(32.dp))

            // Main Face Area
            BingoFaceCard(
                voiceState = voiceState,
                modifier = Modifier.weight(1f)
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Status Indicator (Pill clicável para configurar o IP do servidor)
            val statusColor = when (voiceState) {
                VoiceState.CONNECTED, VoiceState.IDLE, VoiceState.LISTENING, VoiceState.PROCESSING, VoiceState.SPEAKING -> Color.Green
                VoiceState.CONNECTING -> Color.Yellow
                VoiceState.DISCONNECTED, VoiceState.ERROR -> Color.Red
            }
            
            val statusText = when (voiceState) {
                VoiceState.CONNECTING -> "CONECTANDO..."
                VoiceState.DISCONNECTED -> "OFFLINE"
                VoiceState.ERROR -> "ERRO"
                else -> "ONLINE"
            }

            val hostDisplay = serverUrl.removePrefix("ws://").removePrefix("wss://").substringBefore("/")

            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .background(BingoDarkJungle, RoundedCornerShape(16.dp))
                    .clickable { showServerConfigDialog = true }
                    .padding(horizontal = 16.dp, vertical = 8.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(10.dp)
                        .background(statusColor, CircleShape)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "$statusText ($hostDisplay ✎)",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Main Connect Button


            Spacer(modifier = Modifier.height(24.dp))

            // Server Response Text
            Surface(
                modifier = Modifier.fillMaxWidth().height(60.dp),
                color = BingoDarkJungle.copy(alpha = 0.1f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Box(contentAlignment = Alignment.Center, modifier = Modifier.padding(horizontal = 12.dp)) {
                    Text(
                        text = response,
                        color = BingoDarkJungle,
                        fontSize = 13.sp,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(80.dp)) // Space for FAB
        }

        // The Hidden Menu
        BingoMenu(
            onOpenProgram = { target ->
                voiceController.send(Message.openProgram(target))
            },
            musicState = musicState,
            onPlayMusic = {
                voiceController.playMusic()
            }
        )

        // Diálogo de Configuração de Endereço do Servidor
        if (showServerConfigDialog) {
            var tempUrl by remember { mutableStateOf(serverUrl) }
            AlertDialog(
                onDismissRequest = { showServerConfigDialog = false },
                title = { 
                    Text(
                        "Configurar Servidor Bingo", 
                        color = BingoDarkJungle, 
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp
                    ) 
                },
                text = {
                    Column {
                        Text(
                            "IP atual detectado no computador: 192.168.0.27", 
                            fontSize = 13.sp, 
                            color = BingoDarkJungle.copy(alpha = 0.8f)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = tempUrl,
                            onValueChange = { tempUrl = it },
                            label = { Text("Endereço WebSocket") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            val finalUrl = if (!tempUrl.startsWith("ws://") && !tempUrl.startsWith("wss://")) {
                                "ws://$tempUrl"
                            } else tempUrl
                            serverUrl = finalUrl
                            prefs.edit().putString("server_url", finalUrl).apply()
                            voiceController.updateServerUrl(finalUrl)
                            showServerConfigDialog = false
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = BingoTeal,
                            contentColor = BingoDarkJungle
                        )
                    ) {
                        Text("Salvar & Conectar", fontWeight = FontWeight.Bold)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showServerConfigDialog = false }) {
                        Text("Cancelar", color = BingoDarkJungle)
                    }
                },
                containerColor = Color.White,
                shape = RoundedCornerShape(16.dp)
            )
        }
    }
}