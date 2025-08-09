# 📱💻 Руководство по созданию библейского приложения и сайта

## 📋 Содержание
1. [Обзор функций](#обзор-функций)
2. [Android приложение](#android-приложение)
3. [Веб-сайт](#веб-сайт)
4. [Общие компоненты](#общие-компоненты)
5. [База данных](#база-данных)
6. [API и интеграции](#api-и-интеграции)
7. [Развертывание](#развертывание)

---

## 🎯 Обзор функций

### Основные возможности для реализации:
- 📖 **Чтение Библии** - все 66 книг в разных переводах
- 🔍 **Поиск стихов** - быстрый поиск по ссылкам (`Ин 3:16`)
- 🤖 **ИИ помощник** - разбор стихов с лимитами
- 📝 **Закладки** - сохранение стихов с заметками
- 📚 **Планы чтения** - структурированное изучение
- 🎯 **Библейские темы** - тематические подборки
- 📅 **Православный календарь** - праздники и посты
- 🔍 **Поиск по словам** - полнотекстовый поиск
- ⚙️ **Настройки** - переводы, темы оформления
- 👑 **Админ панель** - управление контентом

---

# 📱 Android приложение

## 🛠 Технологический стек

### Рекомендуемые технологии:
- **Язык**: Kotlin (предпочтительно) или Java
- **UI**: Jetpack Compose (современный) или XML layouts
- **Архитектура**: MVVM с Repository pattern
- **БД**: Room Database + SQLite
- **Сеть**: Retrofit + OkHttp
- **Навигация**: Navigation Component
- **DI**: Hilt (Dagger)
- **Асинхронность**: Kotlin Coroutines + Flow

## 📁 Структура проекта

```
app/
├── src/main/
│   ├── java/com/yourname/bibleapp/
│   │   ├── data/
│   │   │   ├── database/
│   │   │   │   ├── entities/
│   │   │   │   │   ├── Book.kt
│   │   │   │   │   ├── Chapter.kt
│   │   │   │   │   ├── Verse.kt
│   │   │   │   │   ├── Bookmark.kt
│   │   │   │   │   ├── ReadingPlan.kt
│   │   │   │   │   └── User.kt
│   │   │   │   ├── dao/
│   │   │   │   │   ├── BibleDao.kt
│   │   │   │   │   ├── BookmarkDao.kt
│   │   │   │   │   └── ReadingPlanDao.kt
│   │   │   │   └── BibleDatabase.kt
│   │   │   ├── repository/
│   │   │   │   ├── BibleRepository.kt
│   │   │   │   ├── BookmarkRepository.kt
│   │   │   │   ├── AIRepository.kt
│   │   │   │   └── CalendarRepository.kt
│   │   │   ├── network/
│   │   │   │   ├── OpenRouterAPI.kt
│   │   │   │   ├── CalendarAPI.kt
│   │   │   │   └── models/
│   │   │   └── preferences/
│   │   │       └── UserPreferences.kt
│   │   ├── domain/
│   │   │   ├── models/
│   │   │   ├── usecases/
│   │   │   └── repositories/
│   │   ├── presentation/
│   │   │   ├── ui/
│   │   │   │   ├── books/
│   │   │   │   │   ├── BooksScreen.kt
│   │   │   │   │   └── BooksViewModel.kt
│   │   │   │   ├── reading/
│   │   │   │   │   ├── ReadingScreen.kt
│   │   │   │   │   └── ReadingViewModel.kt
│   │   │   │   ├── bookmarks/
│   │   │   │   ├── search/
│   │   │   │   ├── plans/
│   │   │   │   ├── themes/
│   │   │   │   ├── calendar/
│   │   │   │   └── settings/
│   │   │   ├── components/
│   │   │   │   ├── VerseCard.kt
│   │   │   │   ├── SearchBar.kt
│   │   │   │   └── NavigationDrawer.kt
│   │   │   └── theme/
│   │   │       ├── Color.kt
│   │   │       ├── Theme.kt
│   │   │       └── Type.kt
│   │   └── utils/
│   │       ├── BibleParser.kt
│   │       ├── DateUtils.kt
│   │       └── Constants.kt
│   └── res/
│       ├── values/
│       │   ├── strings.xml
│       │   ├── colors.xml
│       │   └── themes.xml
│       └── drawable/
└── build.gradle.kts
```

## 🔧 Ключевые компоненты

### 1. Entity классы (Room Database)

```kotlin
// Verse.kt
@Entity(tableName = "verses")
data class Verse(
    @PrimaryKey val id: Int,
    val bookId: Int,
    val chapterNumber: Int,
    val verseNumber: Int,
    val text: String,
    val translation: String
)

// Bookmark.kt
@Entity(tableName = "bookmarks")
data class Bookmark(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val verseId: Int,
    val note: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val tags: String = ""
)
```

### 2. DAO интерфейсы

```kotlin
@Dao
interface BibleDao {
    @Query("SELECT * FROM verses WHERE bookId = :bookId AND chapterNumber = :chapter")
    suspend fun getChapter(bookId: Int, chapter: Int): List<Verse>
    
    @Query("SELECT * FROM verses WHERE text LIKE '%' || :query || '%'")
    suspend fun searchVerses(query: String): List<Verse>
    
    @Query("SELECT * FROM verses WHERE bookId = :bookId AND chapterNumber = :chapter AND verseNumber BETWEEN :startVerse AND :endVerse")
    suspend fun getVerseRange(bookId: Int, chapter: Int, startVerse: Int, endVerse: Int): List<Verse>
}
```

### 3. Repository

```kotlin
class BibleRepository @Inject constructor(
    private val bibleDao: BibleDao,
    private val apiService: BibleApiService
) {
    suspend fun getChapter(bookId: Int, chapter: Int): List<Verse> {
        return bibleDao.getChapter(bookId, chapter)
    }
    
    suspend fun searchVerses(query: String): List<Verse> {
        return bibleDao.searchVerses(query)
    }
    
    suspend fun parseReference(reference: String): List<Verse> {
        // Логика парсинга библейских ссылок (Ин 3:16, Мф 5:3-12)
        val parsed = BibleReferenceParser.parse(reference)
        return bibleDao.getVerseRange(parsed.bookId, parsed.chapter, parsed.startVerse, parsed.endVerse)
    }
}
```

### 4. ViewModel

```kotlin
@HiltViewModel
class ReadingViewModel @Inject constructor(
    private val bibleRepository: BibleRepository,
    private val bookmarkRepository: BookmarkRepository,
    private val aiRepository: AIRepository
) : ViewModel() {
    
    private val _verses = MutableLiveData<List<Verse>>()
    val verses: LiveData<List<Verse>> = _verses
    
    private val _aiExplanation = MutableLiveData<String>()
    val aiExplanation: LiveData<String> = _aiExplanation
    
    fun loadChapter(bookId: Int, chapter: Int) {
        viewModelScope.launch {
            try {
                val verses = bibleRepository.getChapter(bookId, chapter)
                _verses.value = verses
            } catch (e: Exception) {
                // Обработка ошибок
            }
        }
    }
    
    fun getAIExplanation(verses: List<Verse>) {
        viewModelScope.launch {
            try {
                val explanation = aiRepository.explainVerses(verses)
                _aiExplanation.value = explanation
            } catch (e: Exception) {
                // Обработка ошибок
            }
        }
    }
    
    fun addBookmark(verse: Verse, note: String) {
        viewModelScope.launch {
            bookmarkRepository.addBookmark(verse.id, note)
        }
    }
}
```

### 5. Compose UI

```kotlin
@Composable
fun ReadingScreen(
    viewModel: ReadingViewModel = hiltViewModel()
) {
    val verses by viewModel.verses.observeAsState(emptyList())
    val aiExplanation by viewModel.aiExplanation.observeAsState()
    
    LazyColumn {
        items(verses) { verse ->
            VerseCard(
                verse = verse,
                onBookmark = { note -> viewModel.addBookmark(verse, note) },
                onAIExplain = { viewModel.getAIExplanation(listOf(verse)) }
            )
        }
        
        aiExplanation?.let { explanation ->
            item {
                AIExplanationCard(explanation = explanation)
            }
        }
    }
}

@Composable
fun VerseCard(
    verse: Verse,
    onBookmark: (String) -> Unit,
    onAIExplain: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "${verse.verseNumber}. ${verse.text}",
                style = MaterialTheme.typography.body1
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                IconButton(onClick = onAIExplain) {
                    Icon(Icons.Default.Psychology, contentDescription = "ИИ разбор")
                }
                IconButton(onClick = { onBookmark("") }) {
                    Icon(Icons.Default.Bookmark, contentDescription = "Закладка")
                }
            }
        }
    }
}
```

## 🔍 Особенности реализации

### Парсер библейских ссылок

```kotlin
object BibleReferenceParser {
    private val referencePattern = Regex("""(\w+)\s*(\d+):(\d+)(?:-(\d+))?(?:-(\d+):(\d+))?""")
    
    fun parse(reference: String): ParsedReference? {
        val match = referencePattern.find(reference) ?: return null
        
        val bookName = match.groupValues[1]
        val chapter = match.groupValues[2].toInt()
        val startVerse = match.groupValues[3].toInt()
        val endVerse = match.groupValues[4].toIntOrNull() ?: startVerse
        
        return ParsedReference(
            bookId = getBookId(bookName),
            chapter = chapter,
            startVerse = startVerse,
            endVerse = endVerse
        )
    }
}
```

### ИИ интеграция

```kotlin
class AIRepository @Inject constructor(
    private val openRouterAPI: OpenRouterAPI,
    private val userPreferences: UserPreferences
) {
    suspend fun explainVerses(verses: List<Verse>): String {
        if (!checkDailyLimit()) throw AILimitExceededException()
        
        val prompt = buildPrompt(verses)
        val response = openRouterAPI.generateExplanation(prompt)
        
        incrementDailyUsage()
        return response.text
    }
    
    private suspend fun checkDailyLimit(): Boolean {
        val today = LocalDate.now().toString()
        val lastUsageDate = userPreferences.getLastAIUsageDate()
        val usageCount = if (lastUsageDate == today) {
            userPreferences.getAIUsageCount()
        } else 0
        
        return usageCount < AI_DAILY_LIMIT
    }
}
```

## 🎨 UI/UX рекомендации

### Темы оформления
```kotlin
@Composable
fun BibleAppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colors = if (darkTheme) {
        darkColorScheme(
            primary = Color(0xFF6750A4),
            onPrimary = Color.White,
            background = Color(0xFF121212),
            surface = Color(0xFF1E1E1E)
        )
    } else {
        lightColorScheme(
            primary = Color(0xFF6750A4),
            onPrimary = Color.White,
            background = Color(0xFFFFFBFE),
            surface = Color.White
        )
    }
    
    MaterialTheme(
        colorScheme = colors,
        typography = Typography(),
        content = content
    )
}
```

### Навигация
```kotlin
@Composable
fun BibleNavigation() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "books"
    ) {
        composable("books") {
            BooksScreen(
                onBookSelected = { bookId ->
                    navController.navigate("reading/$bookId/1")
                }
            )
        }
        composable("reading/{bookId}/{chapter}") { backStackEntry ->
            val bookId = backStackEntry.arguments?.getString("bookId")?.toInt() ?: 1
            val chapter = backStackEntry.arguments?.getString("chapter")?.toInt() ?: 1
            ReadingScreen(bookId = bookId, chapter = chapter)
        }
        composable("bookmarks") { BookmarksScreen() }
        composable("search") { SearchScreen() }
        composable("plans") { ReadingPlansScreen() }
        composable("themes") { ThemesScreen() }
        composable("calendar") { CalendarScreen() }
        composable("settings") { SettingsScreen() }
    }
}
```

---

# 💻 Веб-сайт

## 🛠 Технологический стек

### Рекомендуемые технологии:
- **Frontend**: React.js + TypeScript
- **UI Framework**: Material-UI или Tailwind CSS
- **State Management**: Redux Toolkit или Zustand
- **Routing**: React Router
- **Build Tool**: Vite или Create React App
- **Backend**: Node.js + Express или Next.js
- **БД**: PostgreSQL + Prisma ORM
- **Auth**: NextAuth.js или Firebase Auth
- **Hosting**: Vercel, Netlify или AWS

## 📁 Структура проекта

```
bible-web-app/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── bible/
│   │   │   ├── BooksGrid.tsx
│   │   │   ├── ChapterView.tsx
│   │   │   ├── VerseCard.tsx
│   │   │   └── BibleNavigation.tsx
│   │   ├── bookmarks/
│   │   │   ├── BookmarksList.tsx
│   │   │   ├── BookmarkCard.tsx
│   │   │   └── AddBookmarkModal.tsx
│   │   ├── ai/
│   │   │   ├── AIExplanation.tsx
│   │   │   └── AILimitIndicator.tsx
│   │   ├── reading-plans/
│   │   │   ├── PlansGrid.tsx
│   │   │   ├── PlanCard.tsx
│   │   │   └── ProgressTracker.tsx
│   │   ├── themes/
│   │   │   ├── ThemesGrid.tsx
│   │   │   └── ThemeCard.tsx
│   │   ├── calendar/
│   │   │   ├── CalendarView.tsx
│   │   │   └── EventCard.tsx
│   │   └── settings/
│   │       ├── SettingsPanel.tsx
│   │       └── TranslationSelector.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── BooksPage.tsx
│   │   ├── ReadingPage.tsx
│   │   ├── BookmarksPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── PlansPage.tsx
│   │   ├── ThemesPage.tsx
│   │   ├── CalendarPage.tsx
│   │   └── SettingsPage.tsx
│   ├── hooks/
│   │   ├── useBible.ts
│   │   ├── useBookmarks.ts
│   │   ├── useAI.ts
│   │   ├── useSearch.ts
│   │   └── useAuth.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── bibleService.ts
│   │   ├── aiService.ts
│   │   ├── bookmarkService.ts
│   │   └── calendarService.ts
│   ├── store/
│   │   ├── slices/
│   │   │   ├── bibleSlice.ts
│   │   │   ├── bookmarksSlice.ts
│   │   │   ├── userSlice.ts
│   │   │   └── settingsSlice.ts
│   │   └── store.ts
│   ├── types/
│   │   ├── bible.ts
│   │   ├── user.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── bibleParser.ts
│   │   ├── dateUtils.ts
│   │   └── constants.ts
│   └── styles/
│       ├── globals.css
│       └── components.css
├── public/
│   ├── icons/
│   └── images/
├── api/ (если используете Next.js)
│   ├── bible/
│   ├── bookmarks/
│   ├── ai/
│   └── calendar/
└── package.json
```

## 🔧 Ключевые компоненты

### 1. React компоненты

```tsx
// ChapterView.tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useBible } from '../hooks/useBible';
import { useAI } from '../hooks/useAI';
import VerseCard from './VerseCard';

interface ChapterViewProps {
  bookId: number;
  chapter: number;
}

const ChapterView: React.FC<ChapterViewProps> = ({ bookId, chapter }) => {
  const { verses, loading, error } = useBible(bookId, chapter);
  const { getExplanation, aiLoading } = useAI();
  const [selectedVerses, setSelectedVerses] = useState<number[]>([]);

  const handleVerseSelect = (verseId: number) => {
    setSelectedVerses(prev => 
      prev.includes(verseId) 
        ? prev.filter(id => id !== verseId)
        : [...prev, verseId]
    );
  };

  const handleAIExplanation = async () => {
    if (selectedVerses.length === 0) return;
    
    const versesToExplain = verses.filter(v => selectedVerses.includes(v.id));
    await getExplanation(versesToExplain);
  };

  if (loading) return <div className="loading-spinner">Загрузка...</div>;
  if (error) return <div className="error">Ошибка: {error}</div>;

  return (
    <div className="chapter-view">
      <div className="chapter-header">
        <h2>Глава {chapter}</h2>
        {selectedVerses.length > 0 && (
          <button 
            onClick={handleAIExplanation}
            disabled={aiLoading}
            className="ai-explain-btn"
          >
            🤖 ИИ разбор ({selectedVerses.length} стихов)
          </button>
        )}
      </div>
      
      <div className="verses-container">
        {verses.map(verse => (
          <VerseCard
            key={verse.id}
            verse={verse}
            selected={selectedVerses.includes(verse.id)}
            onSelect={() => handleVerseSelect(verse.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default ChapterView;
```

### 2. Hooks

```tsx
// useBible.ts
import { useState, useEffect } from 'react';
import { bibleService } from '../services/bibleService';
import { Verse } from '../types/bible';

export const useBible = (bookId: number, chapter: number) => {
  const [verses, setVerses] = useState<Verse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchVerses = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const data = await bibleService.getChapter(bookId, chapter);
        setVerses(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
      } finally {
        setLoading(false);
      }
    };

    fetchVerses();
  }, [bookId, chapter]);

  return { verses, loading, error };
};

// useAI.ts
import { useState } from 'react';
import { aiService } from '../services/aiService';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { incrementAIUsage } from '../store/slices/userSlice';

export const useAI = () => {
  const [explanation, setExplanation] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const aiUsage = useAppSelector(state => state.user.aiUsageToday);
  const dispatch = useAppDispatch();

  const getExplanation = async (verses: Verse[]) => {
    if (aiUsage >= 3) {
      setError('Достигнут дневной лимит ИИ запросов');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await aiService.explainVerses(verses);
      setExplanation(result);
      dispatch(incrementAIUsage());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ошибка ИИ');
    } finally {
      setLoading(false);
    }
  };

  return { explanation, loading, error, getExplanation };
};
```

### 3. Services

```tsx
// bibleService.ts
import { api } from './api';
import { Verse, Book, Chapter } from '../types/bible';

export const bibleService = {
  async getBooks(): Promise<Book[]> {
    const response = await api.get('/bible/books');
    return response.data;
  },

  async getChapter(bookId: number, chapter: number): Promise<Verse[]> {
    const response = await api.get(`/bible/books/${bookId}/chapters/${chapter}`);
    return response.data;
  },

  async searchVerses(query: string): Promise<Verse[]> {
    const response = await api.get(`/bible/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  async parseReference(reference: string): Promise<Verse[]> {
    const response = await api.post('/bible/parse', { reference });
    return response.data;
  }
};

// aiService.ts
import { api } from './api';
import { Verse } from '../types/bible';

export const aiService = {
  async explainVerses(verses: Verse[]): Promise<string> {
    const response = await api.post('/ai/explain', {
      verses: verses.map(v => ({ text: v.text, reference: `${v.book} ${v.chapter}:${v.verse}` }))
    });
    return response.data.explanation;
  },

  async getDailyLimitInfo(): Promise<{ used: number; limit: number }> {
    const response = await api.get('/ai/limits');
    return response.data;
  }
};
```

### 4. Redux Store

```tsx
// store/slices/bibleSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { bibleService } from '../../services/bibleService';
import { Verse, Book } from '../../types/bible';

interface BibleState {
  books: Book[];
  currentVerses: Verse[];
  currentBook: number | null;
  currentChapter: number | null;
  loading: boolean;
  error: string | null;
}

const initialState: BibleState = {
  books: [],
  currentVerses: [],
  currentBook: null,
  currentChapter: null,
  loading: false,
  error: null
};

export const fetchBooks = createAsyncThunk(
  'bible/fetchBooks',
  async () => {
    return await bibleService.getBooks();
  }
);

export const fetchChapter = createAsyncThunk(
  'bible/fetchChapter',
  async ({ bookId, chapter }: { bookId: number; chapter: number }) => {
    return await bibleService.getChapter(bookId, chapter);
  }
);

const bibleSlice = createSlice({
  name: 'bible',
  initialState,
  reducers: {
    setCurrentLocation: (state, action: PayloadAction<{ book: number; chapter: number }>) => {
      state.currentBook = action.payload.book;
      state.currentChapter = action.payload.chapter;
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchBooks.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchBooks.fulfilled, (state, action) => {
        state.loading = false;
        state.books = action.payload;
      })
      .addCase(fetchBooks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Ошибка загрузки книг';
      })
      .addCase(fetchChapter.fulfilled, (state, action) => {
        state.currentVerses = action.payload;
      });
  }
});

export const { setCurrentLocation, clearError } = bibleSlice.actions;
export default bibleSlice.reducer;
```

## 🎨 CSS стили

```css
/* styles/globals.css */
:root {
  --primary-color: #6750A4;
  --secondary-color: #625B71;
  --background-color: #FFFBFE;
  --surface-color: #FFFFFF;
  --text-primary: #1C1B1F;
  --text-secondary: #49454F;
  --border-color: #CAC4D0;
}

[data-theme="dark"] {
  --background-color: #121212;
  --surface-color: #1E1E1E;
  --text-primary: #E6E1E5;
  --text-secondary: #CAC4D0;
  --border-color: #49454F;
}

body {
  background-color: var(--background-color);
  color: var(--text-primary);
  font-family: 'Roboto', sans-serif;
  margin: 0;
  padding: 0;
}

.verse-card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  margin: 8px 0;
  transition: all 0.2s ease;
}

.verse-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.verse-card.selected {
  border-color: var(--primary-color);
  background: rgba(103, 80, 164, 0.1);
}

.ai-explain-btn {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.ai-explain-btn:hover:not(:disabled) {
  background: #5A4FCF;
}

.ai-explain-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
```

## 🔍 Особенности веб-версии

### PWA поддержка
```json
// public/manifest.json
{
  "name": "Библейское приложение",
  "short_name": "Библия",
  "description": "Изучение Священного Писания с ИИ помощником",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#6750A4",
  "theme_color": "#6750A4",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker
```javascript
// public/sw.js
const CACHE_NAME = 'bible-app-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/bible-data.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});
```

---

# 🗄️ Общие компоненты

## 📊 База данных

### Схема PostgreSQL

```sql
-- Книги Библии
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(10) NOT NULL,
    testament VARCHAR(10) NOT NULL, -- 'old' или 'new'
    chapters_count INTEGER NOT NULL,
    book_order INTEGER NOT NULL
);

-- Стихи
CREATE TABLE verses (
    id SERIAL PRIMARY KEY,
    book_id INTEGER REFERENCES books(id),
    chapter_number INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    translation VARCHAR(20) NOT NULL DEFAULT 'rst'
);

-- Пользователи
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_usage_count INTEGER DEFAULT 0,
    ai_usage_date DATE DEFAULT CURRENT_DATE,
    premium_ai_count INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Закладки
CREATE TABLE bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    verse_id INTEGER REFERENCES verses(id),
    note TEXT DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Планы чтения
CREATE TABLE reading_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    duration_days INTEGER NOT NULL,
    plan_data JSONB NOT NULL -- структура плана
);

-- Прогресс пользователей по планам
CREATE TABLE user_reading_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan_id INTEGER REFERENCES reading_plans(id),
    current_day INTEGER DEFAULT 1,
    completed_days INTEGER[] DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, plan_id)
);

-- Библейские темы
CREATE TABLE themes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    verses JSONB NOT NULL -- массив ссылок на стихи
);

-- Православный календарь
CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL, -- 'holiday', 'fast', 'saint'
    importance INTEGER DEFAULT 1 -- 1-5, важность события
);

-- Индексы для производительности
CREATE INDEX idx_verses_book_chapter ON verses(book_id, chapter_number);
CREATE INDEX idx_verses_text_search ON verses USING gin(to_tsvector('russian', text));
CREATE INDEX idx_bookmarks_user ON bookmarks(user_id);
CREATE INDEX idx_calendar_date ON calendar_events(date);
```

## 🔌 API эндпоинты

### Express.js routes

```javascript
// routes/bible.js
const express = require('express');
const router = express.Router();
const { BibleService } = require('../services/BibleService');

// Получить все книги
router.get('/books', async (req, res) => {
    try {
        const books = await BibleService.getBooks();
        res.json(books);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Получить главу
router.get('/books/:bookId/chapters/:chapter', async (req, res) => {
    try {
        const { bookId, chapter } = req.params;
        const { translation = 'rst' } = req.query;
        
        const verses = await BibleService.getChapter(
            parseInt(bookId), 
            parseInt(chapter), 
            translation
        );
        res.json(verses);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Поиск стихов
router.get('/search', async (req, res) => {
    try {
        const { q, translation = 'rst', limit = 50 } = req.query;
        const results = await BibleService.searchVerses(q, translation, parseInt(limit));
        res.json(results);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Парсинг библейской ссылки
router.post('/parse', async (req, res) => {
    try {
        const { reference, translation = 'rst' } = req.body;
        const verses = await BibleService.parseReference(reference, translation);
        res.json(verses);
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

module.exports = router;
```

### Service классы

```javascript
// services/BibleService.js
const { Pool } = require('pg');
const pool = new Pool(/* конфигурация БД */);

class BibleService {
    static async getBooks() {
        const query = 'SELECT * FROM books ORDER BY book_order';
        const result = await pool.query(query);
        return result.rows;
    }

    static async getChapter(bookId, chapter, translation = 'rst') {
        const query = `
            SELECT v.*, b.name as book_name, b.short_name
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE v.book_id = $1 AND v.chapter_number = $2 AND v.translation = $3
            ORDER BY v.verse_number
        `;
        const result = await pool.query(query, [bookId, chapter, translation]);
        return result.rows;
    }

    static async searchVerses(searchText, translation = 'rst', limit = 50) {
        const query = `
            SELECT v.*, b.name as book_name, b.short_name
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE v.translation = $1 
            AND to_tsvector('russian', v.text) @@ plainto_tsquery('russian', $2)
            ORDER BY ts_rank(to_tsvector('russian', v.text), plainto_tsquery('russian', $2)) DESC
            LIMIT $3
        `;
        const result = await pool.query(query, [translation, searchText, limit]);
        return result.rows;
    }

    static async parseReference(reference, translation = 'rst') {
        const parsed = BibleReferenceParser.parse(reference);
        if (!parsed) {
            throw new Error('Неверный формат библейской ссылки');
        }

        const { bookId, chapter, startVerse, endVerse, endChapter } = parsed;
        
        if (endChapter && endChapter !== chapter) {
            // Диапазон между главами
            return await this.getVerseRange(bookId, chapter, startVerse, endChapter, endVerse, translation);
        } else {
            // Обычный диапазон в одной главе
            return await this.getVerseRangeInChapter(bookId, chapter, startVerse, endVerse, translation);
        }
    }

    static async getVerseRangeInChapter(bookId, chapter, startVerse, endVerse, translation) {
        const query = `
            SELECT v.*, b.name as book_name, b.short_name
            FROM verses v
            JOIN books b ON v.book_id = b.id
            WHERE v.book_id = $1 AND v.chapter_number = $2 
            AND v.verse_number BETWEEN $3 AND $4 
            AND v.translation = $5
            ORDER BY v.verse_number
        `;
        const result = await pool.query(query, [bookId, chapter, startVerse, endVerse, translation]);
        return result.rows;
    }
}

module.exports = { BibleService };
```

## 🤖 ИИ интеграция

### OpenRouter клиент

```javascript
// services/AIService.js
const axios = require('axios');

class AIService {
    constructor(apiKey, model = 'mistralai/mistral-small-3.1-24b-instruct:free') {
        this.apiKey = apiKey;
        this.model = model;
        this.baseURL = 'https://openrouter.ai/api/v1';
    }

    async explainVerses(verses, isPremium = false) {
        const versesText = verses.map(v => `${v.book_name} ${v.chapter_number}:${v.verse_number} - ${v.text}`).join('\n');
        
        const role = isPremium ? this.getPremiumRole() : this.getRegularRole();
        const maxTokens = isPremium ? 1200 : 500;

        const prompt = `${role}\n\nТекст для анализа:\n${versesText}`;

        try {
            const response = await axios.post(
                `${this.baseURL}/chat/completions`,
                {
                    model: this.model,
                    messages: [
                        { role: 'user', content: prompt }
                    ],
                    max_tokens: maxTokens,
                    temperature: 0.7
                },
                {
                    headers: {
                        'Authorization': `Bearer ${this.apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            return response.data.choices[0].message.content;
        } catch (error) {
            throw new Error(`Ошибка ИИ: ${error.response?.data?.error?.message || error.message}`);
        }
    }

    getRegularRole() {
        return `Вы — православный богослов и лингвист. 
        Ваша задача — кратко, понятно и уважительно объяснить смысл указанной главы или стиха Библии. 
        Давайте исторический, богословский и языковой контекст, избегайте субъективных оценок и споров. 
        Объяснение должно быть полезно для современного читателя, но не заменять толкования святых отцов. 
        ТРЕБОВАНИЯ К ОТВЕТУ: Напишите краткий анализ объемом 500-700 символов.
        Будьте лаконичны, но информативны. 
        Пишите ТОЛЬКО на русском языке!`;
    }

    getPremiumRole() {
        return `Вы — выдающийся православный богослов, библеист и лингвист, 
        знаток церковной истории и святоотеческого наследия. 
        Ваша задача — дать исчерпывающий, но доступный анализ указанной главы или стиха Библии. 
        Включите в ответ: исторический контекст, богословское значение, связи с другими местами Писания, 
        толкования святых отцов (если уместно), практическое применение для современной духовной жизни. 
        Ответ должен быть глубоким, но понятным для образованного верующего. 
        Избегайте спорных интерпретаций, придерживайтесь православной традиции. 
        ТРЕБОВАНИЯ К ОТВЕТУ: Напишите анализ объемом 1000-1200 символов. 
        Структурируйте ответ с заголовками и подразделами для лучшей читаемости.`;
    }
}

module.exports = { AIService };
```

---

# 🚀 Развертывание

## 📱 Android развертывание

### 1. Подготовка к релизу

```gradle
// app/build.gradle.kts
android {
    compileSdk 34

    defaultConfig {
        applicationId "com.yourname.bibleapp"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.getByName("release")
        }
    }

    signingConfigs {
        create("release") {
            storeFile = file("../keystore/release.keystore")
            storePassword = System.getenv("KEYSTORE_PASSWORD")
            keyAlias = System.getenv("KEY_ALIAS")
            keyPassword = System.getenv("KEY_PASSWORD")
        }
    }
}
```

### 2. Сборка APK

```bash
# Создание release keystore
keytool -genkey -v -keystore release.keystore -alias bible_app -keyalg RSA -keysize 2048 -validity 10000

# Сборка приложения
./gradlew assembleRelease

# Подпись APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore release.keystore app-release-unsigned.apk bible_app

# Оптимизация APK
zipalign -v 4 app-release-unsigned.apk BibleApp.apk
```

### 3. Публикация в Google Play

1. **Создание аккаунта разработчика** (99$ единоразово)
2. **Подготовка метаданных**:
   - Описание приложения
   - Скриншоты (минимум 2 для каждого типа устройства)
   - Иконка приложения (512x512px)
   - Графическое изображение (1024x500px)

3. **Загрузка APK/AAB** в Play Console
4. **Настройка контент-рейтинга** и **целевой аудитории**
5. **Публикация** на тестирование или в продакшен

## 💻 Веб развертывание

### 1. Next.js приложение

```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  env: {
    OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
    DATABASE_URL: process.env.DATABASE_URL,
  },
  images: {
    domains: ['example.com'],
  },
}

module.exports = nextConfig
```

### 2. Vercel развертывание

```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "OPENROUTER_API_KEY": "@openrouter-api-key",
    "DATABASE_URL": "@database-url",
    "NEXTAUTH_SECRET": "@nextauth-secret"
  }
}
```

### 3. Docker контейнер

```dockerfile
# Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["npm", "start"]
```

### 4. CI/CD пайплайн

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test
    
    - name: Build application
      run: npm run build
      env:
        OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v20
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.ORG_ID }}
        vercel-project-id: ${{ secrets.PROJECT_ID }}
        vercel-args: '--prod'
```

## 🔧 Конфигурация окружения

### Environment переменные

```bash
# .env.local (для веб-приложения)
DATABASE_URL="postgresql://user:password@localhost:5432/bible_db"
OPENROUTER_API_KEY="your_openrouter_api_key"
OPENROUTER_PREMIUM_API_KEY="your_premium_api_key"
NEXTAUTH_SECRET="your_nextauth_secret"
NEXTAUTH_URL="http://localhost:3000"

# Для календаря
CALENDAR_API_URL="https://calendar-api.ru"

# Для аналитики
GOOGLE_ANALYTICS_ID="GA_MEASUREMENT_ID"

# Для уведомлений
FIREBASE_PROJECT_ID="your_firebase_project"
FIREBASE_PRIVATE_KEY="your_private_key"
```

---

## 📚 Дополнительные ресурсы

### Библейские данные
- **Синодальный перевод**: Открытые данные на GitHub
- **Современные переводы**: Лицензированные тексты
- **API**: Bible API, Bible Gateway API

### ИИ модели
- **OpenRouter**: Доступ к множеству моделей
- **OpenAI GPT**: Прямая интеграция
- **Anthropic Claude**: Альтернативный вариант

### Православный календарь
- **API календаря**: pravoslavie.ru, azbyka.ru
- **Святцы**: Базы данных святых и праздников

### Монетизация
- **Google Play**: Внутренние покупки, подписки
- **App Store**: In-App Purchases
- **Веб**: Stripe, PayPal интеграция

---

## ✅ Чек-лист запуска

### Android приложение:
- [ ] Настроена архитектура MVVM
- [ ] Интегрирована Room Database
- [ ] Реализован парсер библейских ссылок
- [ ] Добавлена ИИ интеграция
- [ ] Настроены темы оформления
- [ ] Протестировано на разных устройствах
- [ ] Подготовлены метаданные для Play Store
- [ ] Создан подписанный APK/AAB

### Веб-приложение:
- [ ] Настроен React + TypeScript
- [ ] Создан PostgreSQL схема
- [ ] Реализованы API эндпоинты
- [ ] Добавлена аутентификация
- [ ] Настроена PWA поддержка
- [ ] Протестирована адаптивность
- [ ] Настроен CI/CD пайплайн
- [ ] Развернуто на хостинге

### Общее:
- [ ] Импортированы библейские тексты
- [ ] Настроена ИИ интеграция
- [ ] Добавлены православные календарные данные
- [ ] Протестированы все основные функции
- [ ] Создана документация
- [ ] Настроена аналитика и мониторинг

---

*Данное руководство предоставляет полную основу для создания библейского приложения и веб-сайта. Адаптируйте технологии и архитектуру под ваши потребности и опыт команды разработки.*
