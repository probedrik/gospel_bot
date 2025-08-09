package com.bibleapp.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

@Singleton
class UserPreferences @Inject constructor(
    private val context: Context
) {
    companion object {
        private val USER_ID = intPreferencesKey("user_id")
        private val AI_USAGE_COUNT = intPreferencesKey("ai_usage_count")
        private val LAST_AI_USAGE_DATE = stringPreferencesKey("last_ai_usage_date")
        private val SELECTED_TRANSLATION = stringPreferencesKey("selected_translation")
        private val THEME_MODE = stringPreferencesKey("theme_mode")
    }

    suspend fun getUserId(): Int? {
        val userId = context.dataStore.data.first()[USER_ID]
        return if (userId == 0) null else userId
    }

    suspend fun setUserId(userId: Int) {
        context.dataStore.edit { preferences ->
            preferences[USER_ID] = userId
        }
    }

    suspend fun getAIUsageCount(): Int {
        return context.dataStore.data.first()[AI_USAGE_COUNT] ?: 0
    }

    suspend fun setAIUsageCount(count: Int) {
        context.dataStore.edit { preferences ->
            preferences[AI_USAGE_COUNT] = count
        }
    }

    suspend fun getLastAIUsageDate(): String {
        return context.dataStore.data.first()[LAST_AI_USAGE_DATE] ?: ""
    }

    suspend fun setLastAIUsageDate(date: String) {
        context.dataStore.edit { preferences ->
            preferences[LAST_AI_USAGE_DATE] = date
        }
    }

    suspend fun getSelectedTranslation(): String {
        return context.dataStore.data.first()[SELECTED_TRANSLATION] ?: "rst"
    }

    suspend fun setSelectedTranslation(translation: String) {
        context.dataStore.edit { preferences ->
            preferences[SELECTED_TRANSLATION] = translation
        }
    }

    suspend fun getThemeMode(): String {
        return context.dataStore.data.first()[THEME_MODE] ?: "system"
    }

    suspend fun setThemeMode(mode: String) {
        context.dataStore.edit { preferences ->
            preferences[THEME_MODE] = mode
        }
    }
}