package com.bibleapp.data.repository

import com.bibleapp.data.models.Book
import com.bibleapp.data.models.Verse
import com.bibleapp.data.supabase.SupabaseClient
import com.bibleapp.utils.BibleReferenceParser
import io.github.jan.supabase.postgrest.from
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BibleRepository @Inject constructor() {
    private val client = SupabaseClient.client

    suspend fun getAllBooks(): List<Book> {
        return try {
            client.from("books")
                .select()
                .order("book_order")
                .decodeList<Book>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun getChapter(bookId: Int, chapter: Int, translation: String = "rst"): List<Verse> {
        return try {
            client.from("verses")
                .select()
                .eq("book_id", bookId)
                .eq("chapter_number", chapter)
                .eq("translation", translation)
                .order("verse_number")
                .decodeList<Verse>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun searchVerses(query: String, translation: String = "rst", limit: Int = 50): List<Verse> {
        return try {
            client.from("verses")
                .select()
                .eq("translation", translation)
                .textSearch("text", query)
                .limit(limit)
                .decodeList<Verse>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun parseReference(reference: String, translation: String = "rst"): List<Verse> {
        val parsed = BibleReferenceParser.parse(reference) ?: return emptyList()
        return try {
            client.from("verses")
                .select()
                .eq("book_id", parsed.bookId)
                .eq("chapter_number", parsed.chapter)
                .eq("translation", translation)
                .gte("verse_number", parsed.startVerse)
                .lte("verse_number", parsed.endVerse)
                .order("verse_number")
                .decodeList<Verse>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun getBookById(bookId: Int): Book? {
        return try {
            client.from("books")
                .select()
                .eq("id", bookId)
                .decodeSingleOrNull<Book>()
        } catch (e: Exception) {
            null
        }
    }
}