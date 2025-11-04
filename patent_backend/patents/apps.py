from django.apps import AppConfig


class PatentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'patents'
    verbose_name = '특허 검색'
