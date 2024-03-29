from importlib import import_module

__all__ = [
    "setup_message_handler",
]

def setup_message_handler(handler):
    imported = getattr(__import__('message_handlers',fromlist=[handler]), handler)
