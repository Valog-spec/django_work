from typing import Dict

from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format

from core.states import CategoryFormStates, CategoryStates, MainMenuStates
from models.schemas import CreateCategoryRequest
from services.client_api import APIClient

api_client = APIClient()


async def get_title_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для окна ввода названия"""
    if dialog_manager.start_data and "category_name" in dialog_manager.start_data:
        current_name = dialog_manager.start_data["category_name"]
        return {
            "is_editing": True,
            "current_title": current_name,
            "title": f"📝 Редактирование категории\n\nТекущее название: {current_name}\nВведите новое название:",
        }
    else:
        return {
            "is_editing": False,
            "current_title": "",
            "title": "📝 Создание новой категории\n\nВведите название категории:",
        }


async def on_category_name_input(
        message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
) -> None:
    """Обработчик ввода названия категории"""
    if not text.strip():
        await message.answer("❌ Название категории не может быть пустым")
        return
    if dialog_manager.start_data and "current_category_id" in dialog_manager.start_data:
        # Редактирование существующей категории
        category_id = dialog_manager.start_data.get("current_category_id")
        telegram_id = dialog_manager.event.from_user.id
        if category_id:
            category_data = CreateCategoryRequest(name=text.strip())
            success = await api_client.update_category(
                telegram_id, category_id, category_data
            )
            if success:
                await message.answer("✅ Название категории обновлено!")
                await dialog_manager.start(CategoryStates.list)
            else:
                await message.answer("❌ Ошибка при обновлении категории")
    else:
        dialog_manager.dialog_data["category_name"] = text
        await dialog_manager.switch_to(CategoryFormStates.confirm_add)


async def on_confirm_create(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик подтверждения создания категории"""
    category_name = dialog_manager.dialog_data.get("category_name")
    telegram_id = callback.from_user.id
    category_data = CreateCategoryRequest(name=category_name)
    result = await api_client.create_category(telegram_id, category_data)

    if result:
        dialog_manager.dialog_data["created_category"] = result
        await dialog_manager.next()
    else:
        await callback.message.answer(
            "❌ Не удалось создать категорию. "
            "Возможно, категория с таким названием уже существует."
        )
        await dialog_manager.start(MainMenuStates.main)


async def on_success_continue(callback, button, dialog_manager: DialogManager) -> None:
    """Обработчик продолжения после успешного создания категории"""
    await dialog_manager.start(MainMenuStates.main)


async def get_confirm_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для окна подтверждения создания категории"""
    category_name = dialog_manager.dialog_data.get("category_name", "")
    return {"category_name": category_name}


async def get_success_data(dialog_manager: DialogManager, **kwargs) -> Dict:
    """Данные для окна успешного создания категории"""
    category = dialog_manager.dialog_data.get("created_category")
    return {"category_name": category.name if category else ""}


input_name_window = Window(
    Format("{title}"),
    TextInput(id="category_name_input", on_success=on_category_name_input),
    Cancel(Const("❌ Отмена")),
    state=CategoryFormStates.input_name,
    getter=get_title_data,
)

confirm_window = Window(
    Format(
        "✅ Подтвердите создание категории\n\n"
        "Название: {category_name}\n\n"
        "Создать категорию?"
    ),
    Row(
        Button(Const("✅ Создать"), id="confirm", on_click=on_confirm_create),
        Back(Const("✏️ Изменить название")),
    ),
    state=CategoryFormStates.confirm_add,
    getter=get_confirm_data,
)

success_window = Window(
    Format(
        "🎉 Категория успешно создана!\n\n"
        "Категория '{category_name}' готова к использованию.\n\n"
        "Теперь вы можете добавлять задачи в эту категорию."
    ),
    Button(Const("📋 Продолжить"), id="continue", on_click=on_success_continue),
    state=CategoryFormStates.success,
    getter=get_success_data,
)

add_category_dialog = Dialog(
    input_name_window,
    confirm_window,
    success_window,
)
