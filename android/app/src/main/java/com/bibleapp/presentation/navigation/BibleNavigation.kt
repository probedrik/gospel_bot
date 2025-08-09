package com.bibleapp.presentation.navigation

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.Bookmark
import androidx.compose.material.icons.filled.Home
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.bibleapp.presentation.ui.books.BooksScreen
import com.bibleapp.presentation.ui.bookmarks.BookmarksScreen
import com.bibleapp.presentation.ui.reading.ReadingScreen
import com.bibleapp.presentation.ui.setup.SetupScreen

sealed class Screen(val route: String, val title: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    object Setup : Screen("setup", "Настройка", Icons.Default.Home)
    object Books : Screen("books", "Книги", Icons.Default.Book)
    object Bookmarks : Screen("bookmarks", "Закладки", Icons.Default.Bookmark)
    object Reading : Screen("reading/{bookId}/{chapter}", "Чтение", Icons.Default.Home)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BibleNavigation() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    NavHost(
        navController = navController,
        startDestination = Screen.Setup.route
    ) {
        composable(Screen.Setup.route) {
            SetupScreen(
                onSetupComplete = {
                    navController.navigate(Screen.Books.route) {
                        popUpTo(Screen.Setup.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Books.route) {
            MainAppContent(
                currentDestination = currentDestination,
                navController = navController
            )
        }

        composable(Screen.Bookmarks.route) {
            MainAppContent(
                currentDestination = currentDestination,
                navController = navController
            )
        }

        composable("reading/{bookId}/{chapter}") { backStackEntry ->
            val bookId = backStackEntry.arguments?.getString("bookId")?.toIntOrNull() ?: 1
            val chapter = backStackEntry.arguments?.getString("chapter")?.toIntOrNull() ?: 1
            
            ReadingScreen(
                bookId = bookId,
                chapter = chapter
            )
        }
    }
}

@Composable
private fun MainAppContent(
    currentDestination: androidx.navigation.NavDestination?,
    navController: androidx.navigation.NavHostController
) {
    val bottomNavItems = listOf(
        Screen.Books,
        Screen.Bookmarks
    )

    Scaffold(
        bottomBar = {
            NavigationBar {
                bottomNavItems.forEach { screen ->
                    NavigationBarItem(
                        icon = { Icon(screen.icon, contentDescription = null) },
                        label = { Text(screen.title) },
                        selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                        onClick = {
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        }
                    )
                }
            }
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            when (currentDestination?.route) {
                Screen.Books.route -> {
                    BooksScreen(
                        onBookSelected = { bookId ->
                            navController.navigate("reading/$bookId/1")
                        }
                    )
                }
                Screen.Bookmarks.route -> {
                    BookmarksScreen()
                }
            }
        }
    }
}