import logging

from aiogram import Bot
from aiohttp import web

from config.settings import settings

logger = logging.getLogger(__name__)


async def send_message_handler(request):
    try:
        data = await request.json()
        telegram_id = data.get("telegram_id")
        message = data.get("message")

        if not telegram_id or not message:
            return web.json_response(
                {"error": "Необходимы telegram_id и message"}, status=400
            )

        bot = Bot(token=settings.BOT_TOKEN)

        await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")

        logger.info(f"Сообщение успешно отправлено пользователю {telegram_id}")
        return web.json_response({"status": "success"})

    except Exception as e:
        logger.error(f"Ошибка отправки сообщения пользователю {telegram_id}: {e}")
        return web.json_response(
            {"error": f"Не удалось отправить сообщение: {str(e)}"}, status=500
        )


def setup_routes(app):
    app.router.add_post("/send_message", send_message_handler)


async def start_notification_api():
    app = web.Application()
    setup_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", 8001)
    await site.start()

    logger.info("Notification API запущен на порту 8001")
    return runner
