from typing import Dict

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Row, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from core.states import MainMenuStates, TaskFormStates, TaskStates
from services.client_api import APIClient

# from api_client import APIClient


# from states import TaskStates, MainMenuStates

api_client = APIClient()


def format_task(task, index) -> str:
    """Форматирует задачу для отображения в списке"""
    status = "✅" if task.is_completed else "⏳"
    categories = (
        ", ".join([cat.name for cat in task.categories])
        if task.categories
        else "Без категории"
    )
    due_date = (
        f"\n⏰ До: {task.due_date.strftime('%d.%m.%Y %H:%M')}" if task.due_date else ""
    )

    return (
        f"{status} {task.title}\n"
        f"📅 Создана: {task.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"🏷️ Категории: {categories}"
        f"{due_date}"
    )


async def get_tasks_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Получает данные задач для отображения в списке"""
    telegram_id = dialog_manager.event.from_user.id
    tasks = await api_client.get_tasks(telegram_id)

    return {
        "tasks": tasks,
        "tasks_count": len(tasks),
        "completed_count": len([t for t in tasks if t.is_completed]),
        "pending_count": len([t for t in tasks if not t.is_completed]),
    }


async def get_task_detail_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Получает детальные данные выбранной задачи"""
    task_id = dialog_manager.dialog_data.get("selected_task_id")
    telegram_id = dialog_manager.event.from_user.id

    if not task_id:
        return {"has_task": False}

    task = await api_client.get_task_detail(telegram_id, task_id)

    if not task:
        return {"has_task": False}

    description_text = task.description or "Нет описания"
    due_date_text = (
        task.due_date.strftime("%d.%m.%Y %H:%M") if task.due_date else "Не установлен"
    )
    categories_text = (
        ", ".join([cat.name for cat in task.categories])
        if task.categories
        else "Без категории"
    )
    toggle_text = "❌ Отменить выполнение" if task.is_completed else "✅ Выполнить"

    return {
        "task": task,
        "has_task": True,
        "task_status": "✅ Выполнена" if task.is_completed else "⏳ В работе",
        "categories": categories_text,
        "created_at": task.created_at.strftime("%d.%m.%Y %H:%M"),
        "due_date": due_date_text,
        "toggle_text": toggle_text,
        "description_text": description_text,
    }


async def on_task_selected(
    callback, button, dialog_manager: DialogManager, item_id: str
) -> None:
    """Обработчик выбора задачи из списка"""
    task_id = item_id
    dialog_manager.dialog_data["selected_task_id"] = task_id
    await dialog_manager.switch_to(TaskStates.detail)


async def on_toggle_complete(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик переключения статуса выполнения задачи"""
    telegram_id = dialog_manager.event.from_user.id
    task_id = dialog_manager.dialog_data.get("selected_task_id")

    if task_id:
        success = await api_client.toggle_task_completion(telegram_id, task_id)
        if success:
            await dialog_manager.update({})


async def on_delete_task(callback, button, dialog_manager: DialogManager) -> None:
    """Общий обработчик удаления задачи"""
    telegram_id = dialog_manager.event.from_user.id
    task_id = dialog_manager.dialog_data.get("selected_task_id")

    if task_id:
        success = await api_client.delete_task(telegram_id, task_id)
        if success:
            await callback.message.answer("✅ Задача удалена!")
            await dialog_manager.switch_to(TaskStates.list)
        else:
            await callback.message.answer("❌ Ошибка при удалении задачи")


async def on_edit_task(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик начала редактирования задачи"""
    task_id = dialog_manager.dialog_data.get("selected_task_id")
    if task_id:
        # Загружаем текущие данные задачи для редактирования
        telegram_id = dialog_manager.event.from_user.id
        task = await api_client.get_task_detail(telegram_id, task_id)
        if task:
            await dialog_manager.start(
                TaskFormStates.title,
                data={
                    "current_task_id": task_id,
                    "task_title": task.title,
                    "task_description": task.description,
                    "task_due_date": task.due_date,
                    "selected_category_ids": [cat.id for cat in task.categories],
                },
            )


async def on_back_to_list(callback, button, dialog_manager: DialogManager) -> None:
    await dialog_manager.switch_to(TaskStates.list)


task_list_window = Window(
    Format(
        "📋 Ваши задачи\n\n"
        "Всего: {tasks_count} | ✅ Выполнено: {completed_count} | ⏳ Ожидает: {pending_count}\n\n"
        "Выберите задачу для просмотра:"
    ),
    ScrollingGroup(
        Select(
            Format("📝 {item.title}"),
            id="task_select",
            item_id_getter=lambda item: str(item.id),
            items="tasks",
            on_click=on_task_selected,
        ),
        id="task_scroll",
        width=1,
        height=6,
    ),
    Start(Const("⬅️ Назад"), id="back_to_main", state=MainMenuStates.main),
    state=TaskStates.list,
    getter=get_tasks_data,
)

task_detail_window = Window(
    Format(
        "📄 Детали задачи\n\n"
        "Название: {task.title}\n"
        "Описание: {description_text}\n"
        "Статус: {task_status}\n"
        "Категории: {categories}\n"
        "Создана: {created_at}\n"
        "Срок: {due_date}\n"
    ),
    Row(
        Button(
            Format("{toggle_text}"),
            id="toggle_complete",
            on_click=on_toggle_complete,
        ),
        Button(Const("✏️ Редактировать"), id="edit_task", on_click=on_edit_task),
    ),
    Row(
        Button(Const("🗑️ Удалить"), id="delete_task", on_click=on_delete_task),
        Back(Const("⬅️ Назад к списку")),
    ),
    state=TaskStates.detail,
    getter=get_task_detail_data,
)

tasks_dialog = Dialog(task_list_window, task_detail_window)
