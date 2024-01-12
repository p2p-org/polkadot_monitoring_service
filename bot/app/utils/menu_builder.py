from callback_data.main import CbData
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

class MenuBuilder(InlineKeyboardBuilder):
    def __init__(self):
        super().__init__()
        self.sizes = []

    def __add__(self,arg : str = None) -> None:
        if arg:
            if arg.split("=")[0] == 'size':
                self.sizes.append(int(arg.split("=")[1]))

    def _button_main_menu(self, size: int = 1):
        self.button(text="Main menu", callback_data=CbData(dst='main_menu',data="").pack())
        self.sizes.append(1)
    
    def _button_back(self,dst,size: int = 1):
        self.button(text="Back", callback_data=CbData(dst=dst,data="").pack())
        self.sizes.append(1)

    def build(self, button_back: str = None, button_main_menu: bool = False):
        if button_main_menu == True:
            self._button_main_menu(size)

        if button_back:
            self._button_back(button_back)
        
        self.adjust(*self.sizes)
