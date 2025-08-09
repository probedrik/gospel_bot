package com.bibleapp.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bibleapp.data.models.Verse
import com.bibleapp.data.repository.AIRepository
import com.bibleapp.data.repository.BibleRepository
import com.bibleapp.data.repository.BookmarkRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ReadingViewModel @Inject constructor(
    private val bibleRepository: BibleRepository,
    private val bookmarkRepository: BookmarkRepository,
    private val aiRepository: AIRepository
) : ViewModel() {

    private val _verses = MutableStateFlow<List<Verse>>(emptyList())
    val verses: StateFlow<List<Verse>> = _verses.asStateFlow()

    private val _aiExplanation = MutableStateFlow<String?>(null)
    val aiExplanation: StateFlow<String?> = _aiExplanation.asStateFlow()

    private val _loading = MutableStateFlow(false)
    val loading: StateFlow<Boolean> = _loading.asStateFlow()

    private val _aiLoading = MutableStateFlow(false)
    val aiLoading: StateFlow<Boolean> = _aiLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    fun loadChapter(bookId: Int, chapter: Int) {
        viewModelScope.launch {
            _loading.value = true
            _error.value = null
            try {
                val versesList = bibleRepository.getChapter(bookId, chapter)
                _verses.value = versesList
            } catch (e: Exception) {
                _error.value = e.message ?: "Ошибка загрузки главы"
            } finally {
                _loading.value = false
            }
        }
    }

    fun getAIExplanation(verses: List<Verse>) {
        viewModelScope.launch {
            _aiLoading.value = true
            _error.value = null
            try {
                val explanation = aiRepository.explainVerses(verses)
                _aiExplanation.value = explanation
            } catch (e: Exception) {
                _error.value = e.message ?: "Ошибка получения объяснения ИИ"
            } finally {
                _aiLoading.value = false
            }
        }
    }

    fun addBookmark(verse: Verse, note: String) {
        viewModelScope.launch {
            try {
                val success = bookmarkRepository.addBookmark(
                    bookId = verse.bookId,
                    chapterStart = verse.chapterNumber,
                    verseStart = verse.verseNumber,
                    verseEnd = verse.verseNumber,
                    displayText = "${verse.bookId}:${verse.chapterNumber}:${verse.verseNumber}",
                    note = note
                )
                if (!success) {
                    _error.value = "Ошибка добавления закладки"
                }
            } catch (e: Exception) {
                _error.value = e.message ?: "Ошибка добавления закладки"
            }
        }
    }

    fun clearError() {
        _error.value = null
    }

    fun clearAIExplanation() {
        _aiExplanation.value = null
    }
}