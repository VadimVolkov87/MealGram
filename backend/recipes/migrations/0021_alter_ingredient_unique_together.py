# Generated by Django 3.2.16 on 2024-08-28 08:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0020_alter_ingredient_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='ingredient',
            unique_together=set(),
        ),
    ]
