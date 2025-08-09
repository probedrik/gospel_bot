package com.bibleapp.data.repository

import com.bibleapp.data.models.Verse
import com.bibleapp.data.network.AIRequest
import com.bibleapp.data.network.Message
import com.bibleapp.data.network.OpenRouterAPI
import com.bibleapp.data.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AIRepository @Inject constructor(
    private val openRouterAPI: OpenRouterAPI,
    private val userRepository: UserRepository
) {
    companion object {
        private const val AI_DAILY_LIMIT = 3
    }

    private val client = SupabaseClient.client

    suspend fun explainVerses(verses: List<Verse>): String {
        val userId = userRepository.getCurrentUserId() 
            ?: throw AILimitExceededException("Пользователь не авторизован")

        if (!checkDailyLimit(userId)) {
            throw AILimitExceededException("Достигнут дневной лимит ИИ запросов")
        }

        val prompt = buildPrompt(verses)
        val request = AIRequest(
            messages = listOf(
                Message("user", prompt)
            )
        )

        val response = openRouterAPI.generateExplanation(request)
        incrementDailyUsage(userId)
        
        return response.choices.firstOrNull()?.message?.content ?: "Ошибка получения ответа"
    }

    suspend fun getDailyUsage(userId: Int): Int {
        return try {
            val today = LocalDate.now().toString()
            val result = client.from("ai_usage")
                .select("count")
                .eq("user_id", userId)
                .eq("date", today)
                .decodeSingleOrNull<Map<String, Int>>()
            
            result?.get("count") ?: 0
        } catch (e: Exception) {
            0
        }
    }

    private suspend fun checkDailyLimit(userId: Int): Boolean {
        val usage = getDailyUsage(userId)
        return usage < AI_DAILY_LIMIT
    }

    private suspend fun incrementDailyUsage(userId: Int) {
        try {
            val today = LocalDate.now().toString()
            
            // Проверяем существующую запись
            val existing = client.from("ai_usage")
                .select("count")
                .eq("user_id", userId)
                .eq("date", today)
                .decodeSingleOrNull<Map<String, Int>>()

            if (existing != null) {
                // Обновляем существующую запись
                val newCount = existing["count"]!! + 1
                client.from("ai_usage")
                    .update(mapOf("count" to newCount))
                    .eq("user_id", userId)
                    .eq("date", today)
            } else {
                // Создаем новую запись
                client.from("ai_usage")
                    .insert(
                        mapOf(
                            "user_id" to userId,
                            "date" to today,
                            "count" to 1
                        )
                    )
            }
        } catch (e: Exception) {
            // Логируем ошибку, но не прерываем работу
        }
    }

    private fun buildPrompt(verses: List<Verse>): String {
        val versesText = verses.joinToString("\n") { "${it.verseNumber}. ${it.text}" }
        return """
            Пожалуйста, объясни следующие библейские стихи простым и понятным языком:
            
            $versesText
            
            Дай краткое толкование, объясни контекст и практическое применение для современного человека.
        """.trimIndent()
    }
}

class AILimitExceededException(message: String) : Exception(message)