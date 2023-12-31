# Generated by Django 3.2.5 on 2021-07-09 19:35

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('matches_and_ranks', '0005_gamematchmaking'),
    ]

    operations = [
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game', models.CharField(max_length=100)),
                ('is_full', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('team_black', models.ManyToManyField(related_name='team_black', to=settings.AUTH_USER_MODEL)),
                ('team_white', models.ManyToManyField(related_name='team_white', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
