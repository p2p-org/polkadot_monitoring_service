from __main__ import dp, db, bot, admin_chat
from aiogram.types import CallbackQuery,Message,InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

menu_cb = CallbackData('row', 'action', 'chat_id')





from __main__ import dp, db, bot, admin_chat
from callback_query_handlers import promalert,grafana,support
from aiogram.types import CallbackQuery,Message,InlineKeyboardButton,InlineKeyboardMarkup

@dp.message_handler(commands=["start"])
async def command_start(message: Message) -> None:
    if str(message.chat.id).startswith('-'):
        await message.answer("🧑🤝🧑 Group chats are not allowed.\nSorry and have a good day.")
        return

    username = message.chat.username
    chat_id = message.from_user.id
    account_status = db.get_records('account_status','id',chat_id)

    if account_status and account_status == 'off':
        await message.answer(chat_id,"Your account has been disabled 🤷\nSorry and have a good day.")
        return

    menu = InlineKeyboardMarkup()
    buttons = [InlineKeyboardButton(text="Operate over Grafana instances", callback_data=grafana.cb.new(func='grafana_instances',action="")),
               InlineKeyboardButton(text="Operate over Prometheus alerts", callback_data=promalert.cb.new(action='promalert_menu')),
               InlineKeyboardButton(text="Contact us(support)", callback_data=support.cb.new(action='support'))]

    for button in buttons:
        menu.row(button)

    if not account_status:
        await bot.send_message(admin_chat, "Username: @{} ID: {}\nHas just PRE-registered.".format(username,chat_id))
        db.add_account(chat_id,username)

    await message.answer("Hi there 👋\n\n\nWelcome to a validator monitoring bot by P2P.org\n\n\n\n",reply_markup=menu)

