from typing import Dict

from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Row
from aiogram_dialog.widgets.text import Const, Format

from core.states import TaskFormStates
from models.schemas import UpdateTaskRequest
from services.client_api import APIClient

api_client = APIClient()


async def get_edit_confirm_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Получает данные для подтверждения редактирования задачи"""
    task_id = dialog_manager.start_data.get("current_task_id")
    if not task_id:
        return {
            "title": "Ошибка",
            "description": "Не найден ID задачи",
            "due_date": "Не установлен",
            "categories": "Без категории",
            "original_title": "Неизвестно",
        }
    telegram_id = dialog_manager.event.from_user.id

    original_task = await api_client.get_task_detail(telegram_id, task_id)

    if not original_task:
        return {
            "title": "Ошибка",
            "description": "Задача не найдена",
            "due_date": "Не установлен",
            "categories": "Без категории",
            "original_title": "Неизвестно",
        }

    # Получаем обновленные данные или используем оригинальные
    title = dialog_manager.dialog_data.get("task_title", original_task.title)
    description = dialog_manager.dialog_data.get(
        "task_description", original_task.description
    )
    due_date = dialog_manager.dialog_data.get("task_due_date", original_task.due_date)
    selected_category_ids = dialog_manager.dialog_data.get("selected_category_ids")

    categories = dialog_manager.dialog_data.get("available_categories", [])
    if selected_category_ids is not None:
        selected_categories = [
            cat for cat in categories if cat.id in selected_category_ids
        ]
    else:
        selected_categories = original_task.categories

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
        "original_title": original_task.title,
    }


async def on_edit_confirm(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик подтверждения редактирования задачи"""
    telegram_id = dialog_manager.event.from_user.id
    task_id = dialog_manager.start_data.get("current_task_id")

    # Собираем только измененные поля
    update_data = UpdateTaskRequest()

    if "task_title" in dialog_manager.dialog_data:
        update_data.title = dialog_manager.dialog_data["task_title"]

    if "task_description" in dialog_manager.dialog_data:
        update_data.description = dialog_manager.dialog_data["task_description"]

    if "task_due_date" in dialog_manager.dialog_data:
        update_data.due_date = dialog_manager.dialog_data["task_due_date"]

    if "selected_category_ids" in dialog_manager.dialog_data:
        update_data.category_ids = dialog_manager.dialog_data["selected_category_ids"]
    result = await api_client.update_task(telegram_id, task_id, update_data)

    if result:
        await callback.message.answer("✅ Задача успешно обновлена!")
        await dialog_manager.done()
    else:
        await callback.message.answer("❌ Ошибка при обновлении задачи")
        await dialog_manager.done()


async def on_skip_field(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик пропуска поля при редактировании"""
    await dialog_manager.next()


edit_confirm_window = Window(
    Format(
        "✅ Подтвердите обновление задачи:\n\n"
        "Название: {title}\n"
        "Описание: {description}\n"
        "Срок: {due_date}\n"
        "Категории: {categories}\n\n"
        "Всё верно?"
    ),
    Row(
        Button(Const("✅ Обновить"), id="confirm", on_click=on_edit_confirm),
        Back(Const("✏️ Исправить")),
    ),
    state=TaskFormStates.confirm_edit,
    getter=get_edit_confirm_data,
)
