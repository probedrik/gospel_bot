# 🐳 Docker развертывание Gospel Bot

Полное руководство по контейнеризации и развертыванию Библейского Telegram бота.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Сборка образа](#сборка-образа)
- [Публикация на Docker Hub](#публикация-на-docker-hub)
- [Развертывание](#развертывание)
- [Конфигурация](#конфигурация)
- [Мониторинг](#мониторинг)
- [Устранение неполадок](#устранение-неполадок)

## 🚀 Быстрый старт

### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+
- Аккаунт на [Docker Hub](https://hub.docker.com/)

### Запуск из готового образа

```bash
# 1. Создайте .env файл с настройками
cp .env.example .env
# Отредактируйте .env файл

# 2. Запустите бот
docker run -d \
  --name gospel-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  your_username/gospel-bot:latest
```

### Запуск с Docker Compose

```bash
# 1. Настройте .env файл
cp .env.example .env

# 2. Запустите с помощью docker-compose
docker-compose up -d
```

## 🔨 Сборка образа

### Локальная сборка

```bash
# Сборка образа
docker build -t gospel-bot:latest .

# Запуск локального образа
docker run -d --name gospel-bot --env-file .env gospel-bot:latest
```

### Автоматическая сборка и публикация

#### Linux/macOS

```bash
# Сделайте скрипт исполняемым
chmod +x build-and-push.sh

# Запустите сборку и публикацию
./build-and-push.sh your_dockerhub_username latest
```

#### Windows (PowerShell)

```powershell
# Запустите PowerShell скрипт
.\build-and-push.ps1 -Username "your_dockerhub_username" -Tag "latest"
```

## 📤 Публикация на Docker Hub

### Ручная публикация

```bash
# 1. Авторизация в Docker Hub
docker login

# 2. Тегирование образа
docker tag gospel-bot:latest your_username/gospel-bot:latest

# 3. Публикация
docker push your_username/gospel-bot:latest
```

### Автоматическая публикация

Используйте предоставленные скрипты `build-and-push.sh` или `build-and-push.ps1`.

## 🚀 Развертывание

### Локальное развертывание

```bash
# С Docker Compose (рекомендуется)
docker-compose up -d

# Или напрямую с Docker
docker run -d \
  --name gospel-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  your_username/gospel-bot:latest
```

### Развертывание на сервере

#### 1. Подготовка сервера

```bash
# Установка Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Развертывание бота

```bash
# Клонирование репозитория или создание структуры
mkdir gospel-bot && cd gospel-bot

# Создание docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  bible-bot:
    image: your_username/gospel-bot:latest
    container_name: bible-bot
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    environment:
      - TZ=Europe/Moscow
    networks:
      - bot-network
    healthcheck:
      test: ["CMD", "python", "-c", "import asyncio; print('Bot is healthy')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  bot-network:
    driver: bridge
EOF

# Создание .env файла
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_user_id
OPENAI_API_KEY=your_openai_api_key
BIBLE_API_KEY=your_bible_api_key
EOF

# Создание необходимых директорий
mkdir -p data logs

# Запуск
docker-compose up -d
```

### Развертывание в облаке

#### AWS ECS

```bash
# Создание task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Создание сервиса
aws ecs create-service \
  --cluster your-cluster \
  --service-name gospel-bot \
  --task-definition gospel-bot:1 \
  --desired-count 1
```

#### Google Cloud Run

```bash
# Развертывание в Cloud Run
gcloud run deploy gospel-bot \
  --image your_username/gospel-bot:latest \
  --platform managed \
  --region us-central1 \
  --set-env-vars BOT_TOKEN=your_token
```

## ⚙️ Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `ADMIN_USER_ID` | ID администратора | ✅ |
| `OPENAI_API_KEY` | Ключ OpenAI API | ❌ |
| `BIBLE_API_KEY` | Ключ Bible API | ❌ |
| `DATABASE_URL` | URL базы данных | ❌ |
| `LOG_LEVEL` | Уровень логирования | ❌ |

### Пример .env файла

```env
# Основные настройки
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USER_ID=123456789

# API ключи (опционально)
OPENAI_API_KEY=sk-...
BIBLE_API_KEY=your_bible_api_key

# База данных (по умолчанию SQLite)
DATABASE_URL=sqlite:///data/bot.db

# Логирование
LOG_LEVEL=INFO

# Часовой пояс
TZ=Europe/Moscow
```

### Volumes (тома)

- `./data:/app/data` - База данных и пользовательские данные
- `./logs:/app/logs` - Логи приложения

## 📊 Мониторинг

### Проверка состояния

```bash
# Статус контейнера
docker ps

# Логи
docker logs bible-bot

# Логи в реальном времени
docker logs -f bible-bot

# Использование ресурсов
docker stats bible-bot
```

### Health Check

Образ включает встроенную проверку здоровья:

```bash
# Проверка здоровья
docker inspect --format='{{.State.Health.Status}}' bible-bot
```

### Мониторинг с Prometheus

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  bible-bot:
    # ... основная конфигурация
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Бот не запускается

```bash
# Проверьте логи
docker logs bible-bot

# Проверьте переменные окружения
docker exec bible-bot env | grep BOT_TOKEN
```

#### 2. Проблемы с базой данных

```bash
# Проверьте права доступа к volume
ls -la data/

# Пересоздайте контейнер
docker-compose down
docker-compose up -d
```

#### 3. Проблемы с сетью

```bash
# Проверьте сетевые настройки
docker network ls
docker network inspect gospel_bot-network
```

### Отладка

```bash
# Запуск в интерактивном режиме
docker run -it --rm --env-file .env your_username/gospel-bot:latest bash

# Подключение к работающему контейнеру
docker exec -it bible-bot bash

# Проверка Python зависимостей
docker exec bible-bot pip list
```

### Обновление

```bash
# Остановка текущего контейнера
docker-compose down

# Обновление образа
docker pull your_username/gospel-bot:latest

# Запуск обновленной версии
docker-compose up -d
```

## 📈 Масштабирование

### Горизонтальное масштабирование

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  bible-bot:
    image: your_username/gospel-bot:latest
    deploy:
      replicas: 3
    # ... остальная конфигурация
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - bible-bot
```

### Использование с оркестраторами

#### Docker Swarm

```bash
# Инициализация swarm
docker swarm init

# Развертывание стека
docker stack deploy -c docker-compose.yml gospel-bot
```

#### Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gospel-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: gospel-bot
  template:
    metadata:
      labels:
        app: gospel-bot
    spec:
      containers:
      - name: gospel-bot
        image: your_username/gospel-bot:latest
        env:
        - name: BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: token
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Не включайте секреты в образ**
2. **Используйте непривилегированного пользователя** (уже настроено)
3. **Регулярно обновляйте базовый образ**
4. **Сканируйте образ на уязвимости**

```bash
# Сканирование образа
docker scan your_username/gospel-bot:latest
```

### Управление секретами

```bash
# Использование Docker secrets (в Swarm)
echo "your_bot_token" | docker secret create bot_token -

# В docker-compose.yml
secrets:
  bot_token:
    external: true
```

---

**Этот документ содержит все необходимое для успешного развертывания Gospel Bot в Docker контейнере! 🚀** 