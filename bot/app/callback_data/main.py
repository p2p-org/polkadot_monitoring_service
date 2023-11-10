from aiogram.filters.callback_data import CallbackData

class Cb(CallbackData, prefix="main"):
    dst: str
    data: str
