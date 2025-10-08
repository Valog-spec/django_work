from typing import Dict

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Row, ScrollingGroup, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from core.states import CategoryFormStates, CategoryStates, MainMenuStates
from services.client_api import APIClient

api_client = APIClient()


async def get_categories_list_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для списка категорий"""
    telegram_id = dialog_manager.event.from_user.id
    categories = await api_client.get_categories(telegram_id)

    return {
        "categories": categories,
        "categories_count": len(categories),
        "has_categories": len(categories) > 0,
    }


async def get_category_detail_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для деталей категории"""
    category_id = dialog_manager.dialog_data.get("selected_category_id")
    telegram_id = dialog_manager.event.from_user.id

    if not category_id:
        return {"has_category": False}

    category = await api_client.get_category_detail(telegram_id, category_id)
    created_at = (
        category.created_at.strftime("%d.%m.%Y %H:%M")
        if category.created_at
        else "Не установлен"
    )
    if not category:
        return {"has_category": False}

    return {
        "category": category,
        "has_category": True,
        "tasks_count": 0,
        "created_at_text": created_at,  # добавляем отформатированную дату
    }


async def on_category_selected(
    callback, button, dialog_manager: DialogManager, item_id: str
) -> None:
    """Обработчик выбора категории"""
    category_id = item_id
    dialog_manager.dialog_data["selected_category_id"] = category_id
    await dialog_manager.switch_to(CategoryStates.detail)


async def on_edit_category(callback, button, dialog_manager: DialogManager) -> None:
    """Начало редактирования категории"""
    category_id = dialog_manager.dialog_data.get("selected_category_id")
    if category_id:
        # Получаем текущую категорию для предзаполнения
        telegram_id = dialog_manager.event.from_user.id
        category = await api_client.get_category_detail(telegram_id, category_id)
        # category = next((cat for cat in categories if cat.id == category_id), None)
        if category:
            dialog_manager.dialog_data["current_category_name"] = category.name
            await dialog_manager.start(
                CategoryFormStates.input_name,
                data={
                    "current_category_id": category_id,
                    "category_name": category.name,
                },
            )


async def on_delete_category(callback, button, dialog_manager: DialogManager) -> None:
    """Подтверждение удаления категории"""
    await dialog_manager.switch_to(CategoryStates.confirm_delete)


async def on_confirm_delete(callback, button, dialog_manager: DialogManager) -> None:
    """Удаление категории"""
    telegram_id = dialog_manager.event.from_user.id
    category_id = dialog_manager.dialog_data.get("selected_category_id")

    if category_id:
        success = await api_client.delete_category(telegram_id, category_id)
        if success:
            await callback.message.answer("✅ Категория удалена!")
            await dialog_manager.switch_to(CategoryStates.list)
        else:
            await callback.message.answer("❌ Ошибка при удалении категории")


# Окно списка категорий
category_list_window = Window(
    Format(
        "🏷️ Ваши категории\n\n"
        "Всего категорий: {categories_count}\n\n"
        "Выберите категорию для управления:"
    ),
    ScrollingGroup(
        Select(
            Format("📁 {item.name}"),
            id="category_select",
            item_id_getter=lambda item: str(item.id),
            items="categories",
            on_click=on_category_selected,
        ),
        id="category_scroll",
        width=1,
        height=6,
    ),
    Row(
        Start(
            Const("➕ Новая категория"),
            id="add_category",
            state=CategoryFormStates.input_name,
        ),
        Start(Const("⬅️ Назад"), id="back_to_main", state=MainMenuStates.main),
    ),
    state=CategoryStates.list,
    getter=get_categories_list_data,
)

# Окно деталей категории
category_detail_window = Window(
    Format(
        "📋 Детали категории\n\n"
        "Название: {category.name}\n"
        "Создана: {created_at_text}\n"
        "Задач в категории: {tasks_count}\n"
    ),
    Row(
        Button(
            Const("✏️ Изменить название"), id="edit_category", on_click=on_edit_category
        ),
        Button(Const("🗑️ Удалить"), id="delete_category", on_click=on_delete_category),
    ),
    Back(Const("⬅️ Назад к списку")),
    state=CategoryStates.detail,
    getter=get_category_detail_data,
)


# Окно подтверждения удаления
category_confirm_delete_window = Window(
    Format(
        "🗑️ Подтверждение удаления\n\n"
        "Вы уверены что хотите удалить категорию?\n\n"
        "Название: {category.name}\n\n"
        "⚠️ Это действие нельзя отменить!"
    ),
    Row(
        Button(
            Const("✅ Да, удалить"), id="confirm_delete", on_click=on_confirm_delete
        ),
        Back(Const("❌ Отмена")),
    ),
    state=CategoryStates.confirm_delete,
    getter=get_category_detail_data,
)

category_list_dialog = Dialog(
    category_list_window,
    category_detail_window,
    category_confirm_delete_window,
)
