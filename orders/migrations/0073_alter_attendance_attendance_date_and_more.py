# Generated by Django 5.0.7 on 2024-09-07 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0072_alter_attendance_attendance_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='attendance_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='user_id',
            field=models.CharField(max_length=100),
        ),
    ]
