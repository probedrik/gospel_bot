package com.bibleapp.data.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Book(
    val id: Int,
    val name: String,
    @SerialName("short_name") val shortName: String,
    val testament: String, // "old" or "new"
    @SerialName("chapters_count") val chaptersCount: Int,
    @SerialName("book_order") val bookOrder: Int
)