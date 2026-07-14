package com.arthurdiaz.bingo.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.arthurdiaz.bingo.ui.theme.BmoActionRed
import com.arthurdiaz.bingo.ui.theme.BmoDarkJungle
import com.arthurdiaz.bingo.ui.theme.BmoYellow

@Composable
fun BmoMenu(
    onManualRecord: () -> Unit,
    onStopRecord: () -> Unit,
    onOpenProgram: (String) -> Unit,
    isRecording: Boolean
) {
    var expanded by remember { mutableStateOf(false) }

    Box(modifier = Modifier.fillMaxSize()) {
        // Expandable Panel
        AnimatedVisibility(
            visible = expanded,
            enter = slideInVertically(initialOffsetY = { it }) + fadeIn(),
            exit = slideOutVertically(targetOffsetY = { it }) + fadeOut(),
            modifier = Modifier.align(Alignment.BottomCenter)
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = RoundedCornerShape(24.dp),
                color = BmoDarkJungle,
                tonalElevation = 8.dp
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "Controles Extras",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        BmoCircleButton(
                            text = if (isRecording) "Parar" else "Gravar",
                            color = BmoActionRed,
                            onClick = { 
                                if (isRecording) onStopRecord() else onManualRecord() 
                                expanded = false
                            }
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                    HorizontalDivider(color = Color.Gray.copy(alpha = 0.5f))
                    Spacer(modifier = Modifier.height(16.dp))

                    Text("Atalhos", color = Color.Gray)
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = { 
                                onOpenProgram("vivaldi")
                                expanded = false
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = BmoYellow, contentColor = BmoDarkJungle)
                        ) { Text("Browser") }
                        Button(
                            onClick = { 
                                onOpenProgram("konsole")
                                expanded = false
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = BmoYellow, contentColor = BmoDarkJungle)
                        ) { Text("Terminal") }
                    }
                }
            }
        }

        // FAB replacement with BMO style button
        Box(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(24.dp)
        ) {
            Button(
                onClick = { expanded = !expanded },
                modifier = Modifier.size(56.dp),
                shape = CircleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (expanded) BmoActionRed else BmoYellow,
                    contentColor = BmoDarkJungle
                ),
                contentPadding = PaddingValues(0.dp)
            ) {
                Text(if (expanded) "X" else "+", style = MaterialTheme.typography.headlineSmall)
            }
        }
    }
}

@Composable
fun BmoCircleButton(
    text: String,
    color: Color,
    onClick: () -> Unit
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Button(
            onClick = onClick,
            modifier = Modifier.size(64.dp),
            shape = CircleShape,
            colors = ButtonDefaults.buttonColors(containerColor = color),
            contentPadding = PaddingValues(0.dp)
        ) {
            // Empty circle like BMO buttons
        }
        Text(text, color = Color.White, style = MaterialTheme.typography.labelSmall)
    }
}