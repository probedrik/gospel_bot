package com.bibleapp.data.network

import retrofit2.http.Body
import retrofit2.http.Headers
import retrofit2.http.POST

data class AIRequest(
    val model: String = "openai/gpt-3.5-turbo",
    val messages: List<Message>
)

data class Message(
    val role: String,
    val content: String
)

data class AIResponse(
    val choices: List<Choice>
)

data class Choice(
    val message: Message
)

interface OpenRouterAPI {
    @Headers("Content-Type: application/json")
    @POST("chat/completions")
    suspend fun generateExplanation(@Body request: AIRequest): AIResponse
}