# Generated by Django 5.1.5 on 2025-01-21 22:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, null=True)),
                ('classificacao', models.CharField(choices=[('category', 'category'), ('food', 'food'), ('eletronico', 'eletronico')], max_length=200, null=True)),
                ('quantidade', models.PositiveIntegerField(null=True)),
            ],
        ),
    ]
