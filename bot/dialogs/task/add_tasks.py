from datetime import datetime, timedelta
from typing import Dict

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Group, Multiselect, Row
from aiogram_dialog.widgets.text import Const, Format

from core.states import TaskFormStates, MainMenuStates
from dialogs.common_components import get_categories_data, on_categories_selected
from dialogs.task.edit_tasks import edit_confirm_window
from models.schemas import CreateTaskRequest
from services.client_api import APIClient



api_client = APIClient()


async def get_confirm_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Получает данные для подтверждения создания задачи"""

    title = dialog_manager.dialog_data.get("task_title", "")
    description = dialog_manager.dialog_data.get("task_description", "")
    due_date = dialog_manager.dialog_data.get("task_due_date")
    selected_category_ids = dialog_manager.dialog_data.get("selected_category_ids", [])

    categories = dialog_manager.dialog_data.get("available_categories", [])
    selected_categories = [cat for cat in categories if cat.id in selected_category_ids]
    due_date_text = due_date.strftime("%d.%m.%Y %H:%M") if due_date else "Не установлен"
    categories_text = (
        ", ".join([cat.name for cat in selected_categories])
        if selected_categories
        else "Без категории"
    )

    return {
        "title": title,
        "description": description or "Нет описания",
        "due_date": due_date_text,
        "categories": categories_text,
    }


async def on_title_input(message, widget, dialog_manager: DialogManager, text: str) -> None:
    """Обработчик ввода названия задачи"""
    dialog_manager.dialog_data["task_title"] = text
    await dialog_manager.next()


async def get_title_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для окна ввода названия"""
    # Если редактируем - берем текущее название из start_data
    if dialog_manager.start_data and "task_title" in dialog_manager.start_data:
        current_title = dialog_manager.start_data["task_title"]
        return {
            "is_editing": True,
            "current_title": current_title,
            "hint": f"📝 Редактирование задачи\n\nТекущее название: {current_title}\nВведите новое название:",
        }
    else:
        return {
            "is_editing": False,
            "current_title": "",
            "hint": "📝 Добавление новой задачи\n\nВведите название задачи:",
        }


async def on_description_input(
    message, widget, dialog_manager: DialogManager, text: str
) -> None:
    """Обработчик ввода описания задачи"""
    dialog_manager.dialog_data["task_description"] = text
    await dialog_manager.next()


async def on_due_date_selected(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик выбора срока выполнения"""
    button_id = button.widget_id
    if button_id == "no_due_date":
        dialog_manager.dialog_data["task_due_date"] = None
    else:
        # days = int(button_id)
        # due_date = datetime.now() + timedelta(days=days)
        # dialog_manager.dialog_data["task_due_date"] = due_date
        date_mapping = {
            "yesterday": -1,
            "today": 0,
            "tomorrow": 1,
            "in_3_days": 3,
            "in_week": 7,
        }

        if button_id in date_mapping:
            days = date_mapping[button_id]
            due_date = datetime.now() + timedelta(days=days)
            dialog_manager.dialog_data["task_due_date"] = due_date

    await dialog_manager.next()


async def on_confirm(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик подтверждения создания задачи"""
    telegram_id = dialog_manager.event.from_user.id
    task_data = CreateTaskRequest(
        title=dialog_manager.dialog_data.get("task_title"),
        description=dialog_manager.dialog_data.get("task_description"),
        due_date=dialog_manager.dialog_data.get("task_due_date"),
        category_ids=dialog_manager.dialog_data.get("selected_category_ids", []),
    )

    result = await api_client.create_task(telegram_id, task_data)

    if result:
        await callback.message.answer("✅ Задача успешно создана!")
        await dialog_manager.start(MainMenuStates.main)
    else:
        await callback.message.answer("❌ Ошибка при создании задачи")
        await dialog_manager.start(MainMenuStates.main)


title_window = Window(
    Format("{hint}"),
    TextInput(id="title_input", on_success=on_title_input),
    Cancel(Const("❌ Отмена")),
    state=TaskFormStates.title,
    getter=get_title_data,
)

description_window = Window(
    Const("✏️ Введите описание задачи (или отправьте '-' чтобы пропустить):"),
    TextInput(id="description_input", on_success=on_description_input),
    Back(Const("⬅️ Назад")),
    state=TaskFormStates.description,
)

due_date_window = Window(
    Const("📅 Выберите срок выполнения:"),
    Group(
        Button(
            Const("📅 Вчера (для теста)"), id="yesterday", on_click=on_due_date_selected
        ),
        Button(Const("⏰ Сегодня"), id="today", on_click=on_due_date_selected),
        Button(Const("📆 Завтра"), id="tomorrow", on_click=on_due_date_selected),
        Button(Const("🗓️ Через 3 дня"), id="in_3_days", on_click=on_due_date_selected),
        Button(Const("🗓️ Через неделю"), id="in_week", on_click=on_due_date_selected),
        Button(Const("❌ Без срока"), id="no_due_date", on_click=on_due_date_selected),
        width=1,
    ),
    Back(Const("⬅️ Назад")),
    state=TaskFormStates.due_date,
)

categories_window = Window(
    Format("🏷️ Выберите категории (доступно: {categories_count}):\n\n"),
    Multiselect(
        Format("✓ {item.name}"),
        Format("{item.name}"),
        id="categories_select",
        item_id_getter=lambda item: str(item.id),
        items="categories",
        on_state_changed=on_categories_selected,
        min_selected=0,
    ),
    Button(
        Const("⏭️ Пропустить"), id="skip_categories", on_click=lambda c, b, d: d.next()
    ),
    Back(Const("⬅️ Назад")),
    state=TaskFormStates.categories,
    getter=get_categories_data,
)

confirm_add_window = Window(
    Format(
        "✅ Подтвердите создание задачи:\n\n"
        "Название: {title}\n"
        "Описание: {description}\n"
        "Срок: {due_date}\n"
        "Категории: {categories}\n\n"
        "Всё верно?"
    ),
    Row(
        Button(Const("✅ Создать"), id="confirm", on_click=on_confirm),
        Back(Const("✏️ Исправить")),
    ),
    state=TaskFormStates.confirm_add,
    getter=get_confirm_data,
)

add_task_dialog = Dialog(
    title_window,
    description_window,
    due_date_window,
    categories_window,
    confirm_add_window,
    edit_confirm_window,
)
