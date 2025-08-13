package com.bibleapp.data.repository

import com.bibleapp.data.models.Book
import com.bibleapp.data.models.Verse
import com.bibleapp.data.supabase.SupabaseClient
import com.bibleapp.utils.BibleReferenceParser
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Columns
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BibleRepository @Inject constructor() {
    private val client = SupabaseClient.client

    suspend fun getAllBooks(): List<Book> {
        return try {
            client.from("books")
                .select(columns = Columns.list("*"))
                .order(column = "book_order")
                .decodeList<Book>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun getChapter(bookId: Int, chapter: Int, translation: String = "rst"): List<Verse> {
        return try {
            client.from("verses")
                .select(columns = Columns.list("*"))
                .eq(column = "book_id", value = bookId)
                .eq(column = "chapter_number", value = chapter)
                .eq(column = "translation", value = translation)
                .order(column = "verse_number")
                .decodeList<Verse>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun searchVerses(query: String, translation: String = "rst", limit: Int = 50): List<Verse> {
        return try {
            client.from("verses")
                .select(columns = Columns.list("*"))
                .eq(column = "translation", value = translation)
                .textSearch(column = "text", query = query)
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
                .select(columns = Columns.list("*"))
                .eq(column = "book_id", value = parsed.bookId)
                .eq(column = "chapter_number", value = parsed.chapter)
                .eq(column = "translation", value = translation)
                .gte(column = "verse_number", value = parsed.startVerse)
                .lte(column = "verse_number", value = parsed.endVerse)
                .order(column = "verse_number")
                .decodeList<Verse>()
        } catch (e: Exception) {
            emptyList()
        }
    }

    suspend fun getBookById(bookId: Int): Book? {
        return try {
            client.from("books")
                .select(columns = Columns.list("*"))
                .eq(column = "id", value = bookId)
                .decodeSingleOrNull<Book>()
        } catch (e: Exception) {
            null
        }
    }
}