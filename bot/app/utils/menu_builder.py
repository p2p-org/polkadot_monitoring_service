from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

class MenuBuilder(InlineKeyboardBuilder):
    def __init__(self):
        super().__init__()
        self.sizes = []

    def __add__(self,arg : str = None) -> None:
        if arg:
            if arg.split("=")[0] == 'size':
                self.sizes.append(int(arg.split("=")[1]))

    def build(self):
        self.adjust(*self.sizes)
