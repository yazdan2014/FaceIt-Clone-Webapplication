import time

from celery import shared_task
from .models import CustomUser, Profile
from matches_and_ranks.models import Match, games_name_list
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery.result import AsyncResult
from dashagh.celery import app
import json
from datetime import datetime, timezone
from django.core.exceptions import ObjectDoesNotExist

channel_layer = get_channel_layer()


@shared_task(bind=True)
def add(self, x, y):
    return x + y


@shared_task(bind=True)
def match_control(self, match_id):
    datetime_now = datetime.now()
    created_at = datetime.now()
    match = Match.objects.get(id=match_id)
    while ((datetime_now - created_at).total_seconds() < 300
           or not match.teams_are_equal()) or not match.teams_are_full():

        match = Match.objects.get(id=match_id)

        players_usernames = match.get_players()
        for username in players_usernames:
            async_to_sync(channel_layer.group_send)(
                f'gamer_{username}', {
                    'type': 'match_making',
                    'message': json.dumps({'type': 'queueing', 'players_number': len(players_usernames)})
                })
        time.sleep(10)

    match = Match.objects.get(match_id)

    players_usernames = match.get_players()
    if not len(players_usernames) == 0:  # Remember to set the limit for 4-6 people during playing part

        for username in players_usernames:
            async_to_sync(channel_layer.group_send)(
                f'gamer_{username}', {
                    'type': 'match_making',
                    'message': json.dumps({'type': 'match_joined',
                                           'players_usernames': players_usernames,
                                           'players_in_game_usernames': match.get_players_in_game_usernames()})
                })
    else:
        match.delete()


@shared_task(bind=True)
def start_matchmaking(self, username, game):
    match_found = False
    task = create_match.apply_async([game], countdown=120)

    while not match_found:

        match = Match.objects.filter(game=game, started=False, is_full=False).first()
        if match is not None:
            task.revoke()
            match_found = True
        else:
            time.sleep(10)
    print('match was found')
    async_to_sync(channel_layer.group_send)(f'gamer_{username}', {
        'type': 'match_making',
        'message': json.dumps({'type': 'match_found', 'match_id': match.id}),
        'match_found': match.id
    })


@shared_task(bind=True)
def create_match(self, game):
    if game in games_name_list:
        print('game is in the list')
    else:
        print('the game is:', game)
    match = Match.objects.create(game=game, started=False, is_full=False)
    match_model_id = match.id
    print(match_model_id)
    task = match_control.delay(match_model_id)


@shared_task(bind=True)
def cancel_matchmaking(self, username, start_task_id):
    task = AsyncResult(id=start_task_id, app=app)
    task.revoke()

    async_to_sync(channel_layer.group_send)(f'gamer_{username}', {
        'type': 'match_making',
        'message': json.dumps({'type': 'no_match_found'})
    })


@shared_task(bind=True)
def manually_cancel(self, username, cancel_task_id, start_task_id):
    start_task = AsyncResult(id=start_task_id, app=app)
    cancel_task = AsyncResult(id=cancel_task_id, app=app)
    start_task.revoke()
    cancel_task.revoke()

    async_to_sync(channel_layer.group_send)(f'gamer_{username}', {
        'type': 'match_making',
        'message': json.dumps({'type': 'matchmaking_canceled'})
    })
