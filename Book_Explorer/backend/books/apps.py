from django.apps import AppConfig


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.books'
    label = 'books'

    def ready(self):
        import backend.books.signals 
