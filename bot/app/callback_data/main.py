from aiogram.filters.callback_data import CallbackData

class CbData(CallbackData, prefix="main"):
    dst: str
    data: str
