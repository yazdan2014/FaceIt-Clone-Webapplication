# Generated by Django 3.2.5 on 2021-07-09 17:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('matches_and_ranks', '0004_auto_20210709_0753'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameMatchMaking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game', models.CharField(max_length=100)),
                ('is_playing', models.BooleanField(default=False)),
                ('is_searching', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
