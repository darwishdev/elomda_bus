# Generated by Django 5.0.7 on 2024-09-05 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0051_remove_item_list_base_price_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item_list',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
