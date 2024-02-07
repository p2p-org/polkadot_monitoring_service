from __main__ import  bot, db, router, cache
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from forms.accounts import Form
from callback_data.main import CbData
from utils.menu_builder import MenuBuilder

@router.callback_query(CbData.filter(F.dst == 'acc_menu'))
async def acc_menu(query: CallbackQuery):
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    validators = db.get_records('validators', 'id', chat_id)

    acc_max = 15
    
    menu = MenuBuilder()
    
    text = "Here you can mange accounts you would like to track.\n\nFor now we are processing over " + str(cache.count()) + " uniq accounts of validators or collators.\n\n"  

    if not validators:
        text += "☝️ No accounts in portfolio yet."
    else:
        text += '☝️ Accounts in portfolio: ' + str(len(validators.split(' '))) + '\n👉 Maximum possible: ' + str(acc_max) + '\n\n'
        idx = int(query.data.split(':')[3])
        validators = validators.split(' ')
        
        try:
            validator = validators[idx]
        except IndexError:
            idx = 0
            validator = validators[idx]
       
        text += '<b>' + validator + '</b>'
        
        menu.button(text="⏪ Prev", callback_data=CbData(dst="acc_menu", data="", id=idx - 1)) + "size=3"
        menu.button(text="❌ Delete", callback_data=CbData(dst="acc_delete", data=validator[:20], id=0)) + "size=3"
        menu.button(text="Next ⏩", callback_data=CbData(dst="acc_menu", data="", id=idx + 1)) + "size=3"

    menu.button(text="⬅️  Back", callback_data=CbData(dst="sub_menu", data="", id=0).pack()) + "size=2"
    
    if validators:
        if len(validators) < acc_max:
            menu.button(text="➕ Add account", callback_data=CbData(dst="acc_add", data="", id=0).pack()) + "size=2"
        else:
            await query.answer('Maximum amount of accounts reached.')
    else:
        menu.button(text="➕ Add account", callback_data=CbData(dst="acc_add", data="", id=0).pack()) + "size=2"
    
    menu.build()

    try:
        await query.message.edit_text(text, reply_markup=menu.as_markup())
    except TelegramBadRequest:
        pass

    await query.answer()

@router.callback_query(CbData.filter(F.dst == 'acc_add'))
async def acc_add(query: CallbackQuery, state: FSMContext):
    d = await state.get_data()
   
    message_id = query.message.message_id
    chat_id = query.message.chat.id

    menu = MenuBuilder()
    menu.button(text="Back", callback_data=CbData(dst="acc_menu", data="", id=0).pack()) + "size=1"
    menu.build()

    await state.set_state(Form.validators)
    await state.set_data({'chat_id':chat_id, 'message_id':message_id})
    await query.message.edit_text('Please enter first letters of requested validator account(ss58).\n\nPress <b>Back</b> if you changed your mind.\n\n', reply_markup=menu.as_markup())

@router.callback_query(CbData.filter(F.dst == 'acc_save'))
async def acc_save(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id

    validators = db.get_records('validators','id', chat_id)
    validator = cache.get(query.data.split(':')[2])[0]
    
    if not validators:
        validators = validator
    else:
        if validator not in validators:
            validators += ' ' + validator
       
    db.update_record(chat_id, 'validators', validators)

    await query.answer('Account has been added')
    await acc_menu(query)

@router.callback_query(CbData.filter(F.dst == 'acc_delete'))
async def acc_delete(query: CallbackQuery, state: FSMContext):
    chat_id = query.message.chat.id
    acc = query.data.split(':')[2]
    validators = db.get_records('validators', 'id', chat_id).split(' ')
    validator = cache.get(acc)[0]
    
    del validators[validators.index(validator)]
    
    if validators:
        validators = ' '.join(validators)
    else:
        validators = None
    
    db.update_record(chat_id, 'validators', validators)

    await query.answer('Account has been deleted')
    await acc_menu(query)
