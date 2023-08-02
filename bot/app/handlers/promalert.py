from __main__ import dp, db, bot, admin_chat
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class Form(StatesGroup):
    promalert = State()

@dp.message_handler(commands=["promalert"])
async def command_support(message: Message, state: FSMContext) -> None:
    if str(message.chat.id).startswith('-'):
        await message.answer("Group chats are not allowed.\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)
    promalert_status = db.get_records('promalert_status','id',chat_id)
    db.get_records('promalert_status','promalert_status','on')

    if not account_status:
        await message.answer("You have no registered yet.\nPlease call /start.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return
    elif account_status == 'off':
        await message.answer("Your account has been disabled 🤷\nSorry and have a good day.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        return

    if promalert_status == 'on':
        keyboard = [[KeyboardButton(text="Deactivate")],
                    [KeyboardButton(text="Back")]
                ]
         
        await message.answer("We found out that you already activated prometheus alerting.\n\nWould you like to deactivate?",reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,resize_keyboard=True))

    elif promalert_status == 'off':
        keyboard = [[KeyboardButton(text="Activate")],
                    [KeyboardButton(text="Back")]
                ]

        await message.answer("We found out that you have no activated prometheus alerting yet.\n\nWould you like to activate?",reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,resize_keyboard=True))

    await state.set_state(Form.promalert)

@dp.message_handler(state=Form.promalert)
async def process_support(message: Message, state: FSMContext) -> None:
    username = message.chat.username
    chat_id = message.from_user.id
    
    if message.text == 'Back':
        await bot.send_message(chat_id,"Okay.\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
    elif message.text == 'Activate':
        await bot.send_message(chat_id,"Alright 👍\n\nFrom now you will receive some alerts from prometheus.\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        db.update_record(chat_id,'promalert_status','on')

    elif message.text == 'Deactivate':
        await bot.send_message(chat_id,"Alerting from prometheus has been disabled.\n\nFeel free to contact us /support if any questions.",reply_markup=ReplyKeyboardRemove())
        await state.reset_state()
        db.update_record(chat_id,'promalert_status','off')
