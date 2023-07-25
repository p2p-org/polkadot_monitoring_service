from importlib import import_module

__all__ = [
    "setup_webserver_handler",
]

def setup_webserver_handler(handler):
    imported = getattr(__import__('webserver',fromlist=[handler]), handler)
