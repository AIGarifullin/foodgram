# Generated by Django 3.2.3 on 2024-07-12 13:21

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0015_auto_20240708_0848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Количество ингредиентов должно быть не менее 1.'), django.core.validators.MaxValueValidator(10000, 'Количество ингредиентов должно быть не более 10000.')], verbose_name='Количество ингредиентов'),
        ),
    ]
