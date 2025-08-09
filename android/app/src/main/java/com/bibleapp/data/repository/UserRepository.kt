package com.bibleapp.data.repository

import com.bibleapp.data.models.User
import com.bibleapp.data.preferences.UserPreferences
import com.bibleapp.data.supabase.SupabaseClient
import io.github.jan.supabase.postgrest.from
import javax.inject.Inject
import javax.inject.Singleton
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

@Singleton
class UserRepository @Inject constructor(
    private val userPreferences: UserPreferences
) {
    private val client = SupabaseClient.client

    suspend fun getCurrentUserId(): Int? {
        return userPreferences.getUserId()
    }

    suspend fun setCurrentUserId(userId: Int) {
        userPreferences.setUserId(userId)
    }

    suspend fun getUser(userId: Int): User? {
        return try {
            client.from("users")
                .select()
                .eq("user_id", userId)
                .decodeSingleOrNull<User>()
        } catch (e: Exception) {
            null
        }
    }

    suspend fun createUser(
        userId: Int,
        username: String? = null,
        firstName: String? = null
    ): Boolean {
        return try {
            val now = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            val userData = mapOf(
                "user_id" to userId,
                "username" to (username ?: ""),
                "first_name" to (firstName ?: ""),
                "translation" to "rst",
                "response_length" to "full",
                "created_at" to now,
                "last_activity" to now
            )

            client.from("users").upsert(userData)
            setCurrentUserId(userId)
            true
        } catch (e: Exception) {
            false
        }
    }

    suspend fun updateUserTranslation(userId: Int, translation: String): Boolean {
        return try {
            client.from("users")
                .update(mapOf("translation" to translation))
                .eq("user_id", userId)
            true
        } catch (e: Exception) {
            false
        }
    }

    suspend fun updateUserActivity(userId: Int): Boolean {
        return try {
            val now = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            client.from("users")
                .update(mapOf("last_activity" to now))
                .eq("user_id", userId)
            true
        } catch (e: Exception) {
            false
        }
    }

    suspend fun getUserTranslation(userId: Int): String {
        return try {
            val user = getUser(userId)
            user?.translation ?: "rst"
        } catch (e: Exception) {
            "rst"
        }
    }

    suspend fun getUserResponseLength(userId: Int): String {
        return try {
            val user = getUser(userId)
            user?.responseLength ?: "full"
        } catch (e: Exception) {
            "full"
        }
    }
}