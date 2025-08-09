package com.bibleapp.data.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Bookmark(
    val id: Int? = null,
    @SerialName("user_id") val userId: Int,
    @SerialName("book_id") val bookId: Int,
    val chapter: Int? = null,
    @SerialName("chapter_start") val chapterStart: Int,
    @SerialName("chapter_end") val chapterEnd: Int? = null,
    @SerialName("verse_start") val verseStart: Int? = null,
    @SerialName("verse_end") val verseEnd: Int? = null,
    @SerialName("display_text") val displayText: String? = null,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class User(
    val id: Int? = null,
    @SerialName("user_id") val userId: Int,
    val username: String? = null,
    @SerialName("first_name") val firstName: String? = null,
    val translation: String = "rst",
    @SerialName("response_length") val responseLength: String = "full",
    @SerialName("created_at") val createdAt: String,
    @SerialName("last_activity") val lastActivity: String
)