package com.arthurdiaz.bingo.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.arthurdiaz.bingo.ui.theme.BingoActionRed
import com.arthurdiaz.bingo.ui.theme.BingoDarkJungle
import com.arthurdiaz.bingo.ui.theme.BingoYellow

@Composable
fun BingoMenu(
    onOpenProgram: (String) -> Unit
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
                color = BingoDarkJungle,
                tonalElevation = 8.dp
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "Comandos Rápidos",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(16.dp))

                    Text("Programas", color = Color.Gray)
                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        BingoRectButton(
                            text = "Browser",
                            color = BingoYellow,
                            modifier = Modifier.weight(1f),
                            onClick = { 
                                onOpenProgram("vivaldi")
                                expanded = false
                            }
                        )
                        BingoRectButton(
                            text = "Terminal",
                            color = BingoYellow,
                            modifier = Modifier.weight(1f),
                            onClick = { 
                                onOpenProgram("konsole")
                                expanded = false
                            }
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    BingoRectButton(
                        text = "Configurações",
                        color = BingoYellow,
                        modifier = Modifier.fillMaxWidth(),
                        onClick = { 
                            onOpenProgram("system_settings")
                            expanded = false
                        }
                    )
                }
            }
        }

        // FAB replacement with Bingo style button
        Box(
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(24.dp)
        ) {
            Button(
                onClick = { expanded = !expanded },
                modifier = Modifier.size(56.dp),
                shape = RoundedCornerShape(16.dp), // Retro square-ish shape
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (expanded) BingoActionRed else BingoYellow,
                    contentColor = BingoDarkJungle
                ),
                contentPadding = PaddingValues(0.dp)
            ) {
                Text(if (expanded) "✕" else "＋", style = MaterialTheme.typography.headlineSmall)
            }
        }
    }
}

@Composable
fun BingoRectButton(
    text: String,
    color: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(50.dp),
        shape = RoundedCornerShape(12.dp), // Squared with round corners
        colors = ButtonDefaults.buttonColors(
            containerColor = color,
            contentColor = BingoDarkJungle
        )
    ) {
        Text(text, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
    }
}