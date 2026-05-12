from django.apps import AppConfig


class StoreConfig(AppConfig):
    name = "store"

    def ready(self):
        # Create the Tweet singleton at app startup so authentication
        # happens once, not on every store/product creation.
        from .functions.tweet import Tweet

        Tweet()
