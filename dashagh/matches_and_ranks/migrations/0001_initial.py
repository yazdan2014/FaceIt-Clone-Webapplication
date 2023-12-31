# Generated by Django 3.2.4 on 2021-07-06 17:47

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import matches_and_ranks.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Hub',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hub_pic', models.ImageField(upload_to='')),
                ('hub_owner_profile', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='accounts.profile')),
                ('members', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Party',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('party_code', models.CharField(default=matches_and_ranks.models.generate_party_code, max_length=10)),
                ('party_leader', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='party_leader', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Stats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('win', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('lose', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mmr', models.IntegerField(default=1000, validators=[django.core.validators.MinValueValidator(0)])),
                ('rank', models.CharField(max_length=30, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PartyMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('edited', models.BooleanField(default=False)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='matches_and_ranks.party')),
                ('sent_from', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PartyMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='matches_and_ranks.party')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PartyInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('party', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='matches_and_ranks.party')),
                ('sent_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organizer_pic', models.ImageField(upload_to='')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MatchResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game', models.CharField(max_length=30)),
                ('game_result', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='HubSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('game', models.CharField(max_length=200)),
                ('hub_description', models.TextField(blank=True)),
                ('hub_background_pic', models.ImageField(upload_to='')),
                ('invite_only', models.BooleanField(default=False)),
                ('applications_allowed', models.BooleanField(default=False)),
                ('application_instructions', models.TextField(null=True)),
                ('game_required_to_join', models.BooleanField(default=False)),
                ('min_level_to_join', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('max_level_to_join', models.IntegerField(default=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('slots', models.PositiveIntegerField(default=1000, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('subscription_required_to_join', models.BooleanField(default=False)),
                ('hub', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='matches_and_ranks.hub')),
            ],
        ),
    ]
