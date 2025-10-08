
from aiogram_dialog import DialogManager

from core.states import TaskFormStates
from services.client_api import APIClient

api_client = APIClient()


async def on_categories_selected(
    callback, widget, dialog_manager: DialogManager, selected: list
) -> None:
    dialog_manager.dialog_data["selected_category_ids"] = [selected]

    if dialog_manager.start_data and "current_task_id" in dialog_manager.start_data:
        await dialog_manager.switch_to(TaskFormStates.confirm_edit)
    else:
        await dialog_manager.switch_to(TaskFormStates.confirm_add)


async def get_categories_data(dialog_manager: DialogManager, **kwargs) -> dict:
    telegram_id = dialog_manager.event.from_user.id
    categories = await api_client.get_categories(telegram_id)

    dialog_manager.dialog_data["available_categories"] = categories

    return {"categories": categories, "categories_count": len(categories)}
