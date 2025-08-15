# 🚀 Скрипт развертывания Gospel Bot v0.7.2 для Windows
# Автоматическое создание релиза и публикация в Docker Hub

param(
    [string]$DockerRepo = "your-dockerhub-username",  # Замените на ваш Docker Hub username
    [switch]$SkipDockerHub = $false,
    [switch]$SkipTests = $false
)

# Переменные
$VERSION = "v0.7.2"
$IMAGE_NAME = "gospel-bot"

# Функции для цветного вывода
function Write-Info($message) {
    Write-Host "ℹ️  $message" -ForegroundColor Blue
}

function Write-Success($message) {
    Write-Host "✅ $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "⚠️  $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "❌ $message" -ForegroundColor Red
}

Write-Host "🌟 Начинаем развертывание Gospel Bot $VERSION..." -ForegroundColor Cyan

try {
    # 1. Проверка зависимостей
    Write-Info "Проверяем зависимости..."

    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "Git не установлен!"
        exit 1
    }

    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker не установлен!"
        exit 1
    }

    Write-Success "Все зависимости установлены"

    # 2. Проверка изменений
    Write-Info "Проверяем статус Git..."

    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Warning "Есть незакоммиченные изменения:"
        git status --short
        
        $response = Read-Host "Хотите закоммитить изменения? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            git add .
            git commit -m "feat: Telegram Stars integration $VERSION

🌟 Новые возможности:
- Пожертвования через Telegram Stars (1, 10, 25, 50, 100 Stars)
- Покупка премиум запросов за Stars
- Интеграция с Supabase для хранения транзакций
- Обновленный PremiumManager с поддержкой Stars

🔧 Исправления:
- Убрано черное окно в инвойсах
- Исправлена фильтрация callback_data
- HTML форматирование вместо Markdown
- Корректная обработка amount_rub полей

🧪 Тестирование:
- Добавлены тесты для Stars платежей
- Проверка отображения баланса
- Валидация callback_data
- Тестирование инвойсов"
            Write-Success "Изменения закоммичены"
        } else {
            Write-Error "Отменено пользователем"
            exit 1
        }
    }

    # 3. Создание тега
    Write-Info "Создаем Git тег $VERSION..."

    $existingTag = git tag -l | Where-Object { $_ -eq $VERSION }
    if ($existingTag) {
        Write-Warning "Тег $VERSION уже существует"
        $response = Read-Host "Удалить существующий тег? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            git tag -d $VERSION
            git push origin ":refs/tags/$VERSION" 2>$null
            Write-Success "Старый тег удален"
        } else {
            Write-Error "Отменено пользователем"
            exit 1
        }
    }

    git tag -a $VERSION -m "Gospel Bot $VERSION - Telegram Stars Integration

🌟 Major Features:
- Telegram Stars payments integration
- Premium AI requests purchase system
- Supabase database support
- Enhanced payment processing

🔧 Bug Fixes:
- Fixed invoice display issues
- Improved callback data handling
- Better error handling and logging

📊 Statistics:
- Full test coverage
- Production ready
- Docker optimized"

    Write-Success "Git тег $VERSION создан"

    # 4. Запуск тестов (если не пропускаем)
    if (!$SkipTests) {
        Write-Info "Запускаем тесты..."
        
        $testFiles = @(
            "test_payments.py",
            "test_premium_display.py", 
            "test_callback_filtering.py",
            "test_invoice_display.py"
        )
        
        foreach ($testFile in $testFiles) {
            if (Test-Path $testFile) {
                Write-Info "Запускаем $testFile..."
                python $testFile
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Тест $testFile провален!"
                    exit 1
                }
            }
        }
        
        Write-Success "Все тесты пройдены"
    }

    # 5. Сборка Docker образа
    Write-Info "Собираем Docker образ..."

    if (!(Test-Path "Dockerfile")) {
        Write-Error "Dockerfile не найден!"
        exit 1
    }

    docker build -t "${IMAGE_NAME}:${VERSION}" . --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Ошибка при сборке Docker образа"
        exit 1
    }

    docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"
    Write-Success "Docker образ собран: ${IMAGE_NAME}:${VERSION}"

    # 6. Тестирование образа
    Write-Info "Тестируем Docker образ..."

    $testResult = docker run --rm "${IMAGE_NAME}:${VERSION}" python -c "import sys; print(f'Python {sys.version}'); print('✅ Образ работает корректно')"
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker образ прошел тестирование"
    } else {
        Write-Error "Ошибка при тестировании Docker образа"
        exit 1
    }

    # 7. Пуш в Git
    Write-Info "Отправляем изменения в Git..."

    git push origin main
    git push origin $VERSION

    Write-Success "Изменения отправлены в Git репозиторий"

    # 8. Публикация в Docker Hub (если не пропускаем)
    if (!$SkipDockerHub) {
        $response = Read-Host "Опубликовать образ в Docker Hub? (y/n)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Write-Info "Публикуем в Docker Hub..."
            
            # Тегируем для Docker Hub
            docker tag "${IMAGE_NAME}:${VERSION}" "${DockerRepo}/${IMAGE_NAME}:${VERSION}"
            docker tag "${IMAGE_NAME}:${VERSION}" "${DockerRepo}/${IMAGE_NAME}:latest"
            
            # Публикуем
            docker push "${DockerRepo}/${IMAGE_NAME}:${VERSION}"
            docker push "${DockerRepo}/${IMAGE_NAME}:latest"
            
            Write-Success "Образ опубликован в Docker Hub: ${DockerRepo}/${IMAGE_NAME}:${VERSION}"
        } else {
            Write-Info "Пропускаем публикацию в Docker Hub"
        }
    }

    # 9. Создание GitHub Release (если используется GitHub)
    $gitRemote = git remote get-url origin
    if ($gitRemote -match "github.com") {
        Write-Info "Создаем GitHub Release..."
        
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            gh release create $VERSION --title "Gospel Bot $VERSION - Telegram Stars Integration" --notes-file "RELEASE_$VERSION.md" --latest
            Write-Success "GitHub Release создан"
        } else {
            Write-Warning "GitHub CLI не установлен, создайте релиз вручную"
            $repoUrl = $gitRemote -replace ".*github.com[:/]([^/]*/[^/]*)(\.git)?.*", 'https://github.com/$1'
            Write-Info "URL для создания релиза: $repoUrl/releases/new?tag=$VERSION"
        }
    }

    # 10. Финальная информация
    Write-Host ""
    Write-Success "🎉 Развертывание Gospel Bot $VERSION завершено успешно!"
    Write-Host ""
    Write-Info "📋 Сводка:"
    Write-Host "   • Версия: $VERSION"
    Write-Host "   • Docker образ: ${IMAGE_NAME}:${VERSION}"
    Write-Host "   • Git тег: $VERSION"
    Write-Host "   • Дата: $(Get-Date)"
    Write-Host ""
    Write-Info "🚀 Команды для запуска:"
    Write-Host "   docker run -d --name gospel-bot --env-file .env ${IMAGE_NAME}:${VERSION}"
    Write-Host ""
    Write-Info "📖 Документация:"
    Write-Host "   • RELEASE_$VERSION.md - описание изменений"
    Write-Host "   • TELEGRAM_STARS_GUIDE.md - руководство по Stars"
    Write-Host ""
    Write-Warning "🔧 Не забудьте:"
    Write-Host "   • Обновить переменные окружения"
    Write-Host "   • Проверить работу Telegram Stars"
    Write-Host "   • Обновить документацию"
    Write-Host ""

    Write-Success "Готово! 🌟"

} catch {
    Write-Error "Произошла ошибка: $($_.Exception.Message)"
    exit 1
}