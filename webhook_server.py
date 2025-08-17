"""
Веб-сервер для обработки вебхуков ЮKassa
"""
import logging
import asyncio
from aiohttp import web
from aiohttp.web_app import Application
from aiohttp.web_runner import AppRunner, TCPSite

from handlers.yookassa_webhook import yookassa_webhook_endpoint
from database.universal_manager import universal_db_manager as db_manager

logger = logging.getLogger(__name__)

class WebhookServer:
    """Веб-сервер для вебхуков"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
    
    def create_app(self) -> Application:
        """Создает aiohttp приложение"""
        app = web.Application()
        
        # Добавляем маршруты
        app.router.add_post('/webhook/yookassa', yookassa_webhook_endpoint)
        
        # Добавляем health check
        app.router.add_get('/health', self.health_check)
        
        # Добавляем информационный эндпоинт
        app.router.add_get('/', self.info_endpoint)
        
        return app
    
    async def health_check(self, request):
        """Health check эндпоинт"""
        return web.json_response({
            'status': 'ok',
            'service': 'gospel-bot-webhook',
            'version': '0.7.2'
        })
    
    async def info_endpoint(self, request):
        """Информационный эндпоинт"""
        return web.json_response({
            'service': 'Gospel Bot Webhook Server',
            'version': '0.7.2',
            'endpoints': {
                'yookassa_webhook': '/webhook/yookassa',
                'health': '/health'
            },
            'description': 'Webhook server for YooKassa payment processing'
        })
    
    async def start(self):
        """Запускает веб-сервер"""
        try:
            # Инициализируем базу данных
            await db_manager.initialize()
            logger.info("✅ База данных инициализирована")
            
            # Создаем приложение
            self.app = self.create_app()
            
            # Создаем runner
            self.runner = AppRunner(self.app)
            await self.runner.setup()
            
            # Создаем сайт
            self.site = TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"🚀 Webhook сервер запущен на http://{self.host}:{self.port}")
            logger.info(f"📨 YooKassa webhook URL: http://{self.host}:{self.port}/webhook/yookassa")
            logger.info(f"❤️ Health check: http://{self.host}:{self.port}/health")
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска webhook сервера: {e}")
            raise
    
    async def stop(self):
        """Останавливает веб-сервер"""
        try:
            if self.site:
                await self.site.stop()
                logger.info("🛑 Webhook сервер остановлен")
            
            if self.runner:
                await self.runner.cleanup()
            
            # Закрываем соединение с БД
            await db_manager.close()
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки webhook сервера: {e}")

async def run_webhook_server():
    """Запускает webhook сервер"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем и запускаем сервер
    server = WebhookServer()
    
    try:
        await server.start()
        
        # Ждем бесконечно
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await server.stop()

if __name__ == '__main__':
    asyncio.run(run_webhook_server())