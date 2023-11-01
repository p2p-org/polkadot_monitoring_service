from callback_query_handlers import promalert,grafana,support
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup

class Menu():
    def __init__(self):

    def user_main(self)


menu = InlineKeyboardMarkup()
buttons = [InlineKeyboardButton(text="Operate over Grafana instances", callback_data=grafana.cb.new(func='grafana_instances',action="")),
           InlineKeyboardButton(text="Operate over Prometheus alerts", callback_data=promalert.cb.new(action='promalert_menu')),
           InlineKeyboardButton(text="Contact us(support)", callback_data=support.cb.new(action='support'))]

for button in buttons:
    menu.row(button)
