from importlib import import_module

__all__ = [
    "setup_web_app",
]

def setup_web_app(web_app):
    imported = getattr(__import__('web_apps',fromlist=[web_app]), web_app)

    imported.register_app()
