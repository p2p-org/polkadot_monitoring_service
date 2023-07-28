from importlib import import_module

__all__ = [
    "setup_web_apps",
]

def setup_web_handler(web_app):
    imported = getattr(__import__('web_apps',fromlist=[web_app]), web_app)
