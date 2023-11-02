from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from callback_data.main import CbData
from __main__ import grafana_url

class MenuBuilder():
    def __init__(self) -> None:
        self.menu = InlineKeyboardBuilder()

    def _preset_main_menu(self):
        self.menu.button(text="Open Grafana", url=grafana_url)
        self.menu.button(text="Manage Prometheus alerts", callback_data=CbData(dst="promalert",data="").pack())
        self.menu.button(text="Contact us(support)", callback_data=CbData(dst='support',data="").pack())

        self.menu.adjust(1,1,1)

    def _preset_promalert_on(self):
        self.menu.button(text="Enable notifications", callback_data=CbData(dst="promalert_on",data="").pack())
        self.menu.adjust(1)

    def _preset_promalert_off(self):
        self.menu.button(text="Disable notifications", callback_data=CbData(dst="promalert_off",data="").pack())
        self.menu.adjust(1)

    def _preset_sub_rules(self):
        self.menu.button(text="Add subscription", callback_data=CbData(dst="sub_rules",data="0").pack())
        self.menu.adjust(1)
    
    def _preset_sub_list(self):
        self.menu.button(text="My subscriptions", callback_data=CbData(dst="sub_list",data="").pack())
        self.menu.adjust(1)

    def _preset_sub_save(self, data: str = ''):
        self.menu.button(text="Save", callback_data=CbData(dst="sub_save",data=data).pack())
        self.menu.adjust(1)

    def _preset_sub_del(self, data: str = ''):
        self.menu.button(text="Delete", callback_data=CbData(dst="sub_del",data=data).pack())
        self.menu.adjust(1)

    def _preset_sub_filter_edit(self, data: [str] = []):
        for k in data:
            if k != 'alertname':
                self.menu.row(InlineKeyboardButton(text=f"Edit {k}", callback_data=CbData(dst="sub_edit", data=k).pack(), width=1))

    def _preset_rules_list(self, data: [str] = [], navigation: str = '0'):
        skip = int(navigation)
        take = 7

        take = min(len(data) - skip, take)
        for i in range(skip, skip+take):
            self.menu.row(InlineKeyboardButton(text=data[i].alertname, callback_data=CbData(dst="sub_rule", data=data[i].alertname).pack()), width=1)
        if len(data) > take:
            prev_page = skip-take if skip-take >= 0 else len(data)-take
            next_page = skip+take if skip+take < len(data) else 0
            self.menu.row(*(
                InlineKeyboardButton(text="<<", callback_data=CbData(dst="sub_rules", data=str(prev_page)).pack()),
                InlineKeyboardButton(text=">>", callback_data=CbData(dst="sub_rules", data=str(next_page)).pack()),
                InlineKeyboardButton(text="Back", callback_data=CbData(dst="promalert", data="").pack())
            ))
        else:
            self.menu.row(InlineKeyboardButton(text="Back", callback_data=CbData(dst="promalert", data="").pack()))

    def _preset_sub_scroll(self, navigation: str = '0/0'):
        current_page, total_pages = [int(p) for p in navigation.split("/")]
        if total_pages > 1:
            next_page = current_page + 1 if current_page + 1 < total_pages else 0
            prev_page = current_page - 1 if current_page - 1 >= 0 else total_pages - 1
            self.menu.row(*(
                InlineKeyboardButton(text="<<", callback_data=CbData(dst="sub_list", data=f"{prev_page}/{total_pages}").pack()),
                InlineKeyboardButton(text=">>", callback_data=CbData(dst="sub_list", data=f"{next_page}/{total_pages}").pack()),
                InlineKeyboardButton(text="Back", callback_data=CbData(dst="promalert", data="").pack())
            ))
        else:
            self.menu.row(
                InlineKeyboardButton(text="Back", callback_data=CbData(dst="promalert", data="").pack())
            )

    def _preset_support_request(self):
        self.menu.button(text="Ask for help", callback_data=CbData(dst='support_request',data="").pack())
        self.menu.adjust(1)

    def _preset_support_reply_start(self, data=""):
        self.menu.button(text="Start reply", callback_data=CbData(dst='support_reply_start',data=data).pack())
        self.menu.adjust(1)

    def _preset_support_reply_cancel(self, data=""):
        self.menu.button(text="Cancel", callback_data=CbData(dst='support_reply_cancel',data=data).pack())
        self.menu.adjust(1)

    def _preset_support_reply_submit(self, data=""):
        self.menu.button(text="Submit reply", callback_data=CbData(dst='support_reply_submit',data=data).pack())
        self.menu.adjust(1)

    def _preset_support_off(self, data=""):
        self.menu.button(text="Support off", callback_data=CbData(dst='support_off',data=data).pack())
        self.menu.adjust(1)

    def _preset_toggle_ban(self, data=""):
        self.menu.button(text="Ban/Unban", callback_data=CbData(dst='toggle_ban',data=data).pack())
        self.menu.adjust(1)

    def _button_main_menu(self):
        self.menu.button(text="Main menu", callback_data=CbData(dst='main_menu',data="").pack())
        self.menu.adjust(1)

    def _button_back(self,dst):
        self.menu.button(text="Back", callback_data=CbData(dst=dst,data="").pack())
        self.menu.adjust(1)

    def build(self, preset: str = None, button_back: str = None, button_main_menu: bool = False):
        if preset:
            eval('self._preset_' + preset)()

        if button_main_menu == True:
            self._button_main_menu()

        if button_back:
            self._button_back(button_back)
        
        return self.menu

    def add(self, preset: str = None, data: any = None, navigation: str = ''):
        if preset:
            if data != None and navigation != '':
                eval('self._preset_' + preset)(data=data, navigation=navigation)
                return self
            if data != None:
                eval('self._preset_' + preset)(data=data)
                return self
            if navigation != '':
                eval('self._preset_' + preset)(navigation=navigation)
                return self
            eval('self._preset_' + preset)()
        return self
