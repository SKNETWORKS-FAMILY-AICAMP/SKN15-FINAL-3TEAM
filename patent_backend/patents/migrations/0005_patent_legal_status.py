# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patents', '0004_opiniondocument'),
    ]

    operations = [
        migrations.AddField(
            model_name='patent',
            name='legal_status',
            field=models.CharField(blank=True, db_index=True, help_text='등록, 공개, 거절, 취하, 포기, 소멸 등', max_length=50, null=True, verbose_name='법적상태'),
        ),
    ]
