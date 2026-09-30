from aiogram.filters import Command

class NewEvent(Command):
    def __init__(self):
        super().__init__("newevent")

class Pay(Command):
    def __init__(self):
        super().__init__("pay")