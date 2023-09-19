from importlib import import_module

__all__ = [
    "setup_message_form",
]

def setup_message_form(form):
    imported = getattr(__import__('forms',fromlist=[form]), form)
