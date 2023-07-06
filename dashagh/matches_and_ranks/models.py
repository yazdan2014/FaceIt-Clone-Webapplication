import django.db.models.fields
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import enum
import random
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

rank_names = {
    'Division 9': (0, 115),
    'Division 8': (115, 350),
    'Division 7': (350, 500),
    'Division 6': (500, 750),
    'Division 5': (750, 1000),
    'Division 4': (1000, 1250),
    'Division 3': (1250, 1500),
    'Division 2': (1500, 1700),
    'Division one': (1700, 1900),

    'Division Zero': (1900, 6000),
}
MMR_PER_WIN = 60
MMR_PER_WIN_PARTY = 50
MMR_PER_LOSS = -50
MMR_PER_LOSS_PARTY = -40
games_name_list = ['lol', 'dota_2', 'fortnite', 'r6', 'valorant']

class GamesName(enum.Enum):

    lol = 'lol'
    dota_2 = 'dota_2'
    fortnite = 'fortnite'
    r6 = 'r6'
    valorant = 'valorant'


def generate_party_code(length=10):
    source = 'abcdefghijklmnopqrstuvwxyz'
    result = ''
    for _ in range(length):
        result += source[random.randint(0, length)]
    return result


class Organizer(models.Model):
    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE)
    organizer_pic = models.ImageField()


class Hub(models.Model):
    hub_owner_profile = models.ForeignKey('accounts.Profile', on_delete=models.DO_NOTHING)

    members = models.ManyToManyField('accounts.CustomUser')

    hub_pic = models.ImageField()

    objects = models.Manager()

    def __str__(self):
        return f'{self.name}, Owner: {str(self.hub_owner_profile.user)}'


class HubSettings(models.Model):
    hub = models.OneToOneField(Hub, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    game = models.CharField(max_length=200)
    hub_description = models.TextField(blank=True)
    hub_background_pic = models.ImageField()
    invite_only = models.BooleanField(default=False)
    applications_allowed = models.BooleanField(default=False)
    application_instructions = models.TextField(null=True)
    game_required_to_join = models.BooleanField(default=False)
    # This are to change later on
    min_level_to_join = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    max_level_to_join = models.IntegerField(validators=[MinValueValidator(0)], default=10)
    slots = models.PositiveIntegerField(default=1000, validators=[MinValueValidator(1), MaxValueValidator(100)])
    subscription_required_to_join = models.BooleanField(default=False)


class Stats(models.Model):
    win = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    lose = models.IntegerField(validators=[MinValueValidator(0)], default=0)


class MatchResult(models.Model):
    user = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE)
    game = models.CharField(max_length=30)
    game_result = models.BooleanField(default=False)


class Party(models.Model):
    party_leader = models.OneToOneField("accounts.CustomUser", related_name='party_leader', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    party_code = models.CharField(max_length=10, default=generate_party_code)

    def __str__(self):
        return str(self.party_leader)


class PartyMember(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    user = models.OneToOneField("accounts.CustomUser", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} member of {self.party.party_leader.username}\'s party'


class PartyInvite(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    sent_to = models.ForeignKey("accounts.CustomUser", on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.party.party_leader.user.username}\'s party invite to {self.sent_to.username}'


class PartyMessage(models.Model):
    party = models.ForeignKey(Party, on_delete=models.CASCADE)
    sent_from = models.ForeignKey("accounts.CustomUser", on_delete=models.DO_NOTHING)
    message_text = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.party.party_leader.username}\'s party message sent by {self.sent_from.username}'


class Rank(models.Model):
    user = models.OneToOneField("accounts.CustomUser", on_delete=models.CASCADE)
    mmr = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    rank = models.CharField(default='UNRANKED', max_length=100)
    league_num = models.IntegerField(default=1)

    objects = models.Manager()

    def set_mmr(self):
        for rank_name in rank_names:
            if rank_names[rank_name][0] <= self.get_mmr < rank_names[rank_name][1]:
                self.rank = rank_name

            return self.mmr


# class Tournament(models.Model):
#     hub = models.ForeignKey(Hub, on_delete=models.CASCADE)


# class GameCsgo(models.Model):
#     game_username = models.CharField(max_length=150)


class UserGameRegister(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    game_name = models.CharField(max_length=30)
    game_username = models.CharField(max_length=50)
    username_changed = models.BooleanField(default=False)


class UserMatchMakingStatus(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    game = models.CharField(max_length=100)
    is_playing = models.BooleanField(default=False)
    is_searching = models.BooleanField(default=False)
    task_start_id = models.CharField(max_length=300, null=True)
    task_cancel_id = models.CharField(max_length=300, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Match(models.Model):
    game = models.CharField(max_length=100)
    started = models.BooleanField(default=False)
    is_full = models.BooleanField(default=False)
    team_black = models.ManyToManyField('accounts.CustomUser', related_name='team_black')
    team_white = models.ManyToManyField('accounts.CustomUser', related_name='team_white')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.game} match. playing since {self.created_at}'

    def player_numbers(self):
        return self.team_black.all().count() + self.team_white.all().count()

    def get_players(self):
        players_usernames = []
        for player in self.team_white.all(), self.team_black.all():
            players_usernames.append(player.username)
        return players_usernames

    def add_player(self, username):
        if self.player_numbers() < 10:
            User = apps.get_model('accounts.CustomUser')
            try:
                user = User.objects.get(username=username)
            except ObjectDoesNotExist:
                raise ObjectDoesNotExist

            team_white_num = self.team_white.all().count()
            team_black_num = self.team_black.all().count()
            if team_white_num - team_black_num == 0:
                self.team_white.add(user)
            elif team_white_num - team_black_num == 1:
                self.team_black.add(user)
            elif team_white_num - team_black_num == -1:
                self.team_white.add(user)
            if self.player_numbers() == 10:
                self.is_full = True
                self.save()
            user_game_status = UserMatchMakingStatus.objects.get(user=user, game=self.game)
            user_game_status.is_searching = False
            user_game_status.is_playing = True
            user_game_status.save()

            return True
        else:
            return False

    def get_players_in_game_usernames(self):
        player_usernames = self.get_players()
        in_game_usernames = []
        for username in player_usernames:
            user_game_register = UserGameRegister.objects.get(user=username, game_name=self.game)
            in_game_usernames.append(user_game_register.game_username)
        return in_game_usernames

    def teams_are_equal(self):
        if self.team_white.all().count() == self.team_black.all().count():
            return True
        else:
            return False
    def teams_are_full(self):
        if len(self.get_players()) == 10:
            return True
        else:
             return False




