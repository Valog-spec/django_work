import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")
    # API_BASE_URL = "http://127.0.0.1:8000"

    API_TIMEOUT = 30

    MESSAGES = {
        "welcome": "👋 Добро пожаловать в ToDo Bot!\n\nЗдесь вы можете управлять своими задачами.",
        "error": "❌ Произошла ошибка. Попробуйте позже.",
        "no_tasks": "📝 У вас пока нет задач.",
        "task_added": "✅ Задача успешно добавлена!",
        "category_added": "✅ Категория успешно добавлена!",
    }


settings = Settings()
