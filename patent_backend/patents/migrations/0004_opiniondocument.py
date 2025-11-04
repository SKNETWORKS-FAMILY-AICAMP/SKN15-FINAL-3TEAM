# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patents', '0003_rejectdocument'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpinionDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('application_number', models.CharField(db_index=True, max_length=50, verbose_name='출원번호')),
                ('full_text', models.TextField(blank=True, null=True, verbose_name='전체_내용')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='데이터 생성일')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='데이터 수정일')),
            ],
            options={
                'verbose_name': '의견 제출 통지서',
                'verbose_name_plural': '의견 제출 통지서 목록',
                'db_table': 'opinion_documents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='opiniondocument',
            index=models.Index(fields=['application_number'], name='opinion_doc_applica_idx'),
        ),
    ]
