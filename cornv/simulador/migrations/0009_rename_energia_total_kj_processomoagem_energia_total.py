# Generated by Django 5.1.5 on 2025-05-03 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('simulador', '0008_processomoagem_energia_total_kj'),
    ]

    operations = [
        migrations.RenameField(
            model_name='processomoagem',
            old_name='energia_total_kj',
            new_name='energia_total',
        ),
    ]
