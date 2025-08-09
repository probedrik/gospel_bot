package com.bibleapp.utils

object Constants {
    const val OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/"
    const val AI_DAILY_LIMIT = 3
    
    // Переводы Библии
    val BIBLE_TRANSLATIONS = mapOf(
        "rst" to "Русский Синодальный перевод",
        "nrt" to "Новый русский перевод",
        "cars" to "Современный русский перевод"
    )
    
    // Темы оформления
    enum class ThemeMode {
        LIGHT, DARK, SYSTEM
    }
}