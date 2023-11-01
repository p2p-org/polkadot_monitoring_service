from aiogram.filters.callback_data import CallbackData

class Callback(CallbackData,prefix="my"):
    row: str
    action: str
