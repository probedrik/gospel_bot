package com.bibleapp.presentation.ui.reading

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.bibleapp.data.models.Verse
import com.bibleapp.presentation.viewmodel.ReadingViewModel

@Composable
fun ReadingScreen(
    bookId: Int,
    chapter: Int,
    viewModel: ReadingViewModel = hiltViewModel()
) {
    val verses by viewModel.verses.collectAsState()
    val aiExplanation by viewModel.aiExplanation.collectAsState()
    val loading by viewModel.loading.collectAsState()
    val aiLoading by viewModel.aiLoading.collectAsState()
    val error by viewModel.error.collectAsState()

    var selectedVerses by remember { mutableStateOf(setOf<Int>()) }

    LaunchedEffect(bookId, chapter) {
        viewModel.loadChapter(bookId, chapter)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Заголовок главы
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Глава $chapter",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )

            if (selectedVerses.isNotEmpty()) {
                Button(
                    onClick = {
                        val versesToExplain = verses.filter { it.id in selectedVerses }
                        viewModel.getAIExplanation(versesToExplain)
                    },
                    enabled = !aiLoading
                ) {
                    if (aiLoading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Icon(Icons.Default.Psychology, contentDescription = null)
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("ИИ разбор (${selectedVerses.size})")
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        when {
            loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            error != null -> {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    )
                ) {
                    Text(
                        text = "Ошибка: $error",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer
                    )
                }
            }
            else -> {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(verses) { verse ->
                        VerseCard(
                            verse = verse,
                            selected = verse.id in selectedVerses,
                            onSelect = { 
                                selectedVerses = if (verse.id in selectedVerses) {
                                    selectedVerses - verse.id
                                } else {
                                    selectedVerses + verse.id
                                }
                            },
                            onBookmark = { note -> 
                                viewModel.addBookmark(verse, note)
                            }
                        )
                    }

                    aiExplanation?.let { explanation ->
                        item {
                            AIExplanationCard(
                                explanation = explanation,
                                onDismiss = { viewModel.clearAIExplanation() }
                            )
                        }
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun VerseCard(
    verse: Verse,
    selected: Boolean,
    onSelect: () -> Unit,
    onBookmark: (String) -> Unit
) {
    Card(
        onClick = onSelect,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            }
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = "${verse.verseNumber}. ${verse.text}",
                style = MaterialTheme.typography.bodyLarge
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                IconButton(onClick = { onBookmark("") }) {
                    Icon(
                        Icons.Default.Bookmark,
                        contentDescription = "Добавить закладку"
                    )
                }
            }
        }
    }
}

@Composable
fun AIExplanationCard(
    explanation: String,
    onDismiss: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "🤖 ИИ разбор",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                TextButton(onClick = onDismiss) {
                    Text("Закрыть")
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = explanation,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}