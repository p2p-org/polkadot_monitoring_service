from callback_data.main import CbData
from __main__ import router
from aiogram.types import CallbackQuery
from utils.menu_builder import MenuBuilder
from aiogram import F

def main_menu():
    return 'Please select', MenuBuilder().build(preset='main_menu')

@router.callback_query(CbData.filter(F.dst == 'main_menu'))
async def menu_prom_cb_handler(query: CallbackQuery):

    text, keyboard = main_menu()

    call = query.message.edit_text(text=text, reply_markup=keyboard.as_markup())
    await query.bot(call)
    await query.answer('main menu')
