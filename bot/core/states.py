from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    main = State()
    about = State()


class TaskFormStates(StatesGroup):
    title = State()
    description = State()
    due_date = State()
    categories = State()
    confirm_add = State()
    confirm_edit = State()


class TaskStates(StatesGroup):
    list = State()
    detail = State()


class CategoryStates(StatesGroup):
    list = State()
    detail = State()
    confirm_delete = State()


class CategoryFormStates(StatesGroup):
    input_name = State()
    confirm_add = State()
    success = State()
