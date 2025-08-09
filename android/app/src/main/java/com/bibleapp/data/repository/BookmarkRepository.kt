package com.bibleapp.data.repository

import com.bibleapp.data.models.Bookmark
import com.bibleapp.data.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import javax.inject.Inject
import javax.inject.Singleton
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

@Singleton
class BookmarkRepository @Inject constructor(
    private val userRepository: UserRepository
) {
    private val client = SupabaseClient.client

    fun getAllBookmarks(): Flow<List<Bookmark>> = flow {
        try {
            val userId = userRepository.getCurrentUserId()
            if (userId != null) {
                val bookmarks = client.from("bookmarks")
                    .select()
                    .eq("user_id", userId)
                    .order("created_at", ascending = false)
                    .decodeList<Bookmark>()
                emit(bookmarks)
            } else {
                emit(emptyList())
            }
        } catch (e: Exception) {
            emit(emptyList())
        }
    }

    suspend fun addBookmark(
        bookId: Int,
        chapterStart: Int,
        chapterEnd: Int? = null,
        verseStart: Int? = null,
        verseEnd: Int? = null,
        displayText: String? = null,
        note: String? = null
    ): Boolean {
        return try {
            val userId = userRepository.getCurrentUserId() ?: return false
            
            val bookmark = mapOf(
                "user_id" to userId,
                "book_id" to bookId,
                "chapter" to chapterStart, // для совместимости
                "chapter_start" to chapterStart,
                "chapter_end" to chapterEnd,
                "verse_start" to verseStart,
                "verse_end" to verseEnd,
                "display_text" to displayText,
                "note" to note,
                "created_at" to LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            )

            client.from("bookmarks").insert(bookmark)
            true
        } catch (e: Exception) {
            false
        }
    }

    suspend fun updateBookmark(bookmark: Bookmark): Boolean {
        return try {
            val userId = userRepository.getCurrentUserId() ?: return false
            
            if (bookmark.id != null && bookmark.userId == userId) {
                client.from("bookmarks")
                    .update(
                        mapOf(
                            "note" to bookmark.note,
                            "display_text" to bookmark.displayText
                        )
                    )
                    .eq("id", bookmark.id)
                    .eq("user_id", userId)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }

    suspend fun deleteBookmark(bookmark: Bookmark): Boolean {
        return try {
            val userId = userRepository.getCurrentUserId() ?: return false
            
            if (bookmark.id != null && bookmark.userId == userId) {
                client.from("bookmarks")
                    .delete()
                    .eq("id", bookmark.id)
                    .eq("user_id", userId)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            false
        }
    }

    suspend fun isBookmarked(
        bookId: Int,
        chapterStart: Int,
        chapterEnd: Int? = null,
        verseStart: Int? = null,
        verseEnd: Int? = null
    ): Boolean {
        return try {
            val userId = userRepository.getCurrentUserId() ?: return false
            
            var query = client.from("bookmarks")
                .select("id")
                .eq("user_id", userId)
                .eq("book_id", bookId)
                .eq("chapter_start", chapterStart)

            if (chapterEnd != null) {
                query = query.eq("chapter_end", chapterEnd)
            }
            if (verseStart != null) {
                query = query.eq("verse_start", verseStart)
            }
            if (verseEnd != null) {
                query = query.eq("verse_end", verseEnd)
            }

            val result = query.decodeList<Map<String, Any>>()
            result.isNotEmpty()
        } catch (e: Exception) {
            false
        }
    }
}