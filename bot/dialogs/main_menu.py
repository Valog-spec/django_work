from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import ShowMode
from aiogram_dialog.widgets.kbd import Button, Group, SwitchTo
from aiogram_dialog.widgets.text import Const

from core.states import (
    CategoryFormStates,
    CategoryStates,
    MainMenuStates,
    TaskFormStates,
    TaskStates,
)
from services.client_api import APIClient

# from states import MainMenuStates, AddCategoryStates, TaskStates, AddTaskStates
# from api_client import APIClient

api_client = APIClient()

main_menu_window = Window(
    Const("📋 Главное меню ToDo Bot\n\nВыберите действие:"),
    Group(
        Button(
            Const("📝 Мои задачи"),
            id="my_tasks",
            on_click=lambda c, b, d: d.start(
                TaskStates.list, mode=StartMode.RESET_STACK
            ),
        ),
        Button(
            Const("🏷️ Мои категории"),
            id="my_categories",
            on_click=lambda c, b, d: d.start(CategoryStates.list),
        ),
        Button(
            Const("➕ Добавить задачу"),
            id="add_task",
            on_click=lambda c, b, d: d.start(
                TaskFormStates.title, mode=StartMode.RESET_STACK
            ),
        ),
        Button(
            Const("🏷️ Создать категорию"),
            id="add_category",
            on_click=lambda c, b, d: d.start(
                CategoryFormStates.input_name, mode=StartMode.RESET_STACK
            ),
        ),
        Button(
            Const("ℹ️ О боте"),
            id="about",
            on_click=lambda c, b, d: d.switch_to(MainMenuStates.about),
        ),
        width=1,
    ),
    state=MainMenuStates.main,
)

about_window = Window(
    Const(
        "🤖 ToDo Bot\n\n"
        "Этот бот поможет вам управлять вашими задачами.\n\n"
        "Возможности:\n"
        "• 📝 Просмотр задач\n"
        "• ✅ Отметка выполнения\n"
        "• 🏷️ Категории задач\n"
        "• ⏰ Напоминания\n\n"
        "Используйте кнопки ниже для навигации."
    ),
    SwitchTo(Const("⬅️ Назад"), id="back_to_main", state=MainMenuStates.main),
    state=MainMenuStates.about,
)

main_menu_dialog = Dialog(main_menu_window, about_window)


async def on_startup(bot: Bot):
    print("Bot started!")


async def start_command(message: Message, dialog_manager: DialogManager) -> None:
    user = message.from_user

    success = await api_client.register_telegram_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    if success:
        await message.answer("👋 Добро пожаловать! Ваш аккаунт успешно подключен.")
        await dialog_manager.start(
            MainMenuStates.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT
        )
    else:
        # Если регистрация не удалась, все равно запускаем бота, но с предупреждением
        await message.answer(
            "⚠️ Произошла ошибка при подключении к системе. "
            "Некоторые функции могут быть недоступны. Попробуйте позже."
        )
        await dialog_manager.start(
            MainMenuStates.main, mode=StartMode.RESET_STACK, show_mode=ShowMode.EDIT
        )
