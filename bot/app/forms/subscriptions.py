from aiogram.filters.state import State, StatesGroup

class Form(StatesGroup):
    subscriptions = State()
