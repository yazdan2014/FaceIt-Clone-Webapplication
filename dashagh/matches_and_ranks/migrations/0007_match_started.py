# Generated by Django 3.2.5 on 2021-07-09 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches_and_ranks', '0006_match'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='started',
            field=models.BooleanField(default=False),
        ),
    ]
