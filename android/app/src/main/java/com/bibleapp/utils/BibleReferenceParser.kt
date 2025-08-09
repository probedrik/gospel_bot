package com.bibleapp.utils

data class ParsedReference(
    val bookId: Int,
    val chapter: Int,
    val startVerse: Int,
    val endVerse: Int
)

object BibleReferenceParser {
    private val referencePattern = Regex("""(\w+)\s*(\d+):(\d+)(?:-(\d+))?""")
    
    private val bookNames = mapOf(
        "быт" to 1, "исх" to 2, "лев" to 3, "чис" to 4, "втор" to 5,
        "нав" to 6, "суд" to 7, "руф" to 8, "1цар" to 9, "2цар" to 10,
        "3цар" to 11, "4цар" to 12, "1пар" to 13, "2пар" to 14, "езд" to 15,
        "неем" to 16, "есф" to 17, "иов" to 18, "пс" to 19, "прит" to 20,
        "еккл" to 21, "песн" to 22, "ис" to 23, "иер" to 24, "плач" to 25,
        "иез" to 26, "дан" to 27, "ос" to 28, "иоил" to 29, "ам" to 30,
        "авд" to 31, "ион" to 32, "мих" to 33, "наум" to 34, "авв" to 35,
        "соф" to 36, "агг" to 37, "зах" to 38, "мал" to 39,
        "мф" to 40, "мк" to 41, "лк" to 42, "ин" to 43, "деян" to 44,
        "рим" to 45, "1кор" to 46, "2кор" to 47, "гал" to 48, "еф" to 49,
        "флп" to 50, "кол" to 51, "1фес" to 52, "2фес" to 53, "1тим" to 54,
        "2тим" to 55, "тит" to 56, "флм" to 57, "евр" to 58, "иак" to 59,
        "1пет" to 60, "2пет" to 61, "1ин" to 62, "2ин" to 63, "3ин" to 64,
        "иуд" to 65, "откр" to 66
    )

    fun parse(reference: String): ParsedReference? {
        val match = referencePattern.find(reference.lowercase()) ?: return null
        
        val bookName = match.groupValues[1]
        val chapter = match.groupValues[2].toIntOrNull() ?: return null
        val startVerse = match.groupValues[3].toIntOrNull() ?: return null
        val endVerse = match.groupValues[4].toIntOrNull() ?: startVerse
        
        val bookId = getBookId(bookName) ?: return null
        
        return ParsedReference(
            bookId = bookId,
            chapter = chapter,
            startVerse = startVerse,
            endVerse = endVerse
        )
    }
    
    private fun getBookId(bookName: String): Int? {
        return bookNames[bookName.lowercase()]
    }
}