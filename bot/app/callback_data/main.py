from aiogram.filters.callback_data import CallbackData

class CbData(CallbackData, prefix="default"):
    dst: str
    data: str
    id: int
