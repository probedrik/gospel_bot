package com.bibleapp.data.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Verse(
    val id: Int,
    @SerialName("book_id") val bookId: Int,
    @SerialName("chapter_number") val chapterNumber: Int,
    @SerialName("verse_number") val verseNumber: Int,
    val text: String,
    val translation: String = "rst"
)