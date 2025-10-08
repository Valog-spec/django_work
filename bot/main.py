import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram_dialog import setup_dialogs

from config.settings import settings
from dialogs.category.add_category import add_category_dialog
from dialogs.category.category import category_list_dialog
from dialogs.task.add_tasks import add_task_dialog
from dialogs.task.tasks import tasks_dialog

from services.notification_service import start_notification_api
from dialogs.main_menu import main_menu_dialog, start_command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    if not settings.BOT_TOKEN:
        raise ValueError("BOT_TOKEN не установлен в переменных окружения")

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    await start_notification_api()
    dp.message.register(start_command, CommandStart())

    dp.include_router(main_menu_dialog)
    dp.include_router(tasks_dialog)
    dp.include_router(add_task_dialog)
    dp.include_router(add_category_dialog)
    dp.include_router(category_list_dialog)

    setup_dialogs(dp)

    logger.info("Бот запущен!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
