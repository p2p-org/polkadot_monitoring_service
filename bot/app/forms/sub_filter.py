from __main__ import router, db
from utils.db import DB
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from utils.menu_builder import MenuBuilder
from utils.msg_text import dict2text

assert isinstance(db, DB)

class Form(StatesGroup):
    sub_filter = State()

@router.message(Form.sub_filter)
async def handle_sub_filter_input(message: Message, state: FSMContext) -> None:
    chat_id = message.from_user.id
    d = await state.get_data()
    await state.clear()
    rule_name = d.get("rule")
    if message.text and message.text != 'Back':
        matchers = []
        if rule_name != 'any':
            matchers.append(('alertname', rule_name))
        m = message.text.strip().replace(',', '\n')
        d['current'][d['expect']] = []
        for line in m.splitlines():
            if line != '':
                d['current'][d['expect']].append(line)
        ######
        keyboard = MenuBuilder()
        keyboard.add(preset='sub_filter_edit', data=d['current'])
        keyboard.add(preset='sub_save', data=d['current']['alertname'][0])
        text = f'<b>{d["expect"]} updated</b>. Review changes and press Save to subscribe or Back to cancel.\n' 
        await message.bot.send_message(text=text+dict2text(d['current']), chat_id=chat_id, reply_markup=keyboard.build(button_back='promalert').as_markup())
    else:
        pass

def sub_filter_input_validate(expected: str, got: [str]) -> (bool, str):
    if expected == 'account':
        if got == ['any']:
            return False, 'Filter "any" for "account" is to open it will cause too many notifications.'
    return True, ''