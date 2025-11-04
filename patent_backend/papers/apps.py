from django.apps import AppConfig


class PapersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'papers'
    verbose_name = '논문 검색'
