# Generated by Django 3.2.5 on 2021-07-09 14:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('matches_and_ranks', '0003_auto_20210709_0720'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_name', models.CharField(max_length=30)),
                ('game_username', models.CharField(max_length=50)),
                ('username_changed', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='FortniteStats',
        ),
        migrations.RemoveField(
            model_name='gamefortnite',
            name='user',
        ),
        migrations.RemoveField(
            model_name='gamerainbow',
            name='user',
        ),
        migrations.RemoveField(
            model_name='gamevalorant',
            name='user',
        ),
        migrations.DeleteModel(
            name='RainbowStats',
        ),
        migrations.DeleteModel(
            name='ValorantStats',
        ),
        migrations.DeleteModel(
            name='GameFortnite',
        ),
        migrations.DeleteModel(
            name='GameRainbow',
        ),
        migrations.DeleteModel(
            name='GameValorant',
        ),
    ]
