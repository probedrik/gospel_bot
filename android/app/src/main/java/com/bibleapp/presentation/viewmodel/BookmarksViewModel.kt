package com.bibleapp.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bibleapp.data.models.Bookmark
import com.bibleapp.data.repository.BookmarkRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class BookmarksViewModel @Inject constructor(
    private val bookmarkRepository: BookmarkRepository
) : ViewModel() {

    private val _bookmarks = MutableStateFlow<List<Bookmark>>(emptyList())
    val bookmarks: StateFlow<List<Bookmark>> = _bookmarks.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    init {
        loadBookmarks()
    }

    private fun loadBookmarks() {
        viewModelScope.launch {
            bookmarkRepository.getAllBookmarks().collect { bookmarksList ->
                _bookmarks.value = bookmarksList
            }
        }
    }

    fun deleteBookmark(bookmark: Bookmark) {
        viewModelScope.launch {
            try {
                val success = bookmarkRepository.deleteBookmark(bookmark)
                if (!success) {
                    _error.value = "Ошибка удаления закладки"
                }
            } catch (e: Exception) {
                _error.value = e.message ?: "Ошибка удаления закладки"
            }
        }
    }

    fun updateBookmark(bookmark: Bookmark) {
        viewModelScope.launch {
            try {
                val success = bookmarkRepository.updateBookmark(bookmark)
                if (!success) {
                    _error.value = "Ошибка обновления закладки"
                }
            } catch (e: Exception) {
                _error.value = e.message ?: "Ошибка обновления закладки"
            }
        }
    }

    fun clearError() {
        _error.value = null
    }
}