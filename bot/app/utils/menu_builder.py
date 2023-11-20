from __main__ import bot,db
from aiogram.utils.keyboard import InlineKeyboardBuilder

class MenuBuilder():
    def _preset_main_menu(self,callback_data):
        self.menu.button(text="Operate over Grafana instances", callback_data=callback_data(dst="grafana",data="").pack())
        self.menu.button(text="Operate over Prometheus alerts", callback_data=callback_data(dst="promalert",data="").pack())
        self.menu.button(text="Contact us(support)", callback_data=callback_data(dst='support',data="").pack())

        self.menu.adjust(1,1,1)

    def _preset_promalert(self,callback_data):

        return self.menu

    def _preset_grafana_on(self,callback_data):
      self.menu.button(text="Setup grafana", callback_data=callback_data(dst="grafana_on",data="").pack())
      self.menu.adjust(1)

    def _preset_grafana_off(self,callback_data):
      self.menu.button(text="Delete grafana", callback_data=callback_data(dst="grafana_off",data="").pack())
      self.menu.adjust(1)

    def _preset_subscribtions(self,callback_data):

        return self.menu

    def _preset_support_on(self,callback_data):
        self.menu.button(text="Contact us", callback_data=callback_data(dst='support_on',data="").pack())
        self.menu.adjust(1)

    def _support_reply(self,callback_data):
        self.menu.button(text="Reply to client", callback_data=callback_data(dst='support_reply',data="").pack())
        self.menu.adjust(1)

    def _button_main_menu(self,callback_data):
        self.menu.button(text="Main menu", callback_data=callback_data(dst='main_menu',data="").pack())
        self.menu.adjust(1)

    def _button_back(self,callback_data,dst):
        self.menu.button(text="Back", callback_data=callback_data(dst=dst,data="").pack())
        self.menu.adjust(1)

    def build(self,callback_data=None,preset: str = None, button_back: str = None, button_main_menu: bool = False):
        self.menu = InlineKeyboardBuilder()

        if preset:
            eval('self._preset_' + preset)(callback_data)

        if button_main_menu == True:
            self._button_main_menu(callback_data)

        if button_back:
            self._button_back(callback_data,button_back)
        
        return self.menu
