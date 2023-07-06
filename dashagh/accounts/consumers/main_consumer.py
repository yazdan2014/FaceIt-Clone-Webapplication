from channels.consumer import AsyncConsumer

from channels.exceptions import StopConsumer
from channels.db import database_sync_to_async
import json

from accounts.models import CustomUser, Profile, FriendRequest
from matches_and_ranks.models import Party, UserGameRegister, UserMatchMakingStatus, Match
from news.models import Message
from django.db.models import Q

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
# Celery
from accounts.tasks import start_matchmaking, cancel_matchmaking, manually_cancel
from celery.result import AsyncResult
from dashagh.celery import app


class MainConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.group_name = f'gamer_{self.user.username}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.send({
            'type': 'websocket.accept',

        })
        await self.set_user_online()

    async def websocket_disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.set_user_offline()
        raise StopConsumer

    async def websocket_receive(self, event):
        text_data = event.get('text', None)

        if text_data:
            text_data_json = json.loads(text_data)
            message_type = text_data_json['type']

            if message_type == 'friend_message':
                # the only things that  should always  be sent for this type are edited and sent_to
                # if edited is True then you should only have message_id and new_text
                # if not you should have text and  sent_to in order to create a message model
                # remember that this all will be saved as models so you should add it to the view Yazdan
                edited = text_data_json['edited']  # default false
                sent_to = text_data_json['sent_to']
                if edited:
                    message_id = text_data_json['message_id']
                    new_text = text_data_json['new_text']
                    message = await self.edit_message(pk=message_id, new_text=new_text, sent_to=sent_to)
                else:
                    text = ['text']

                    message = await self.friend_send_message(sent_to=sent_to, text=text)

                await self.channel_layer.group_send(
                    f'gamer_{sent_to}', {
                        'type': 'friend_message',
                        'message': json.dumps({'type': 'friend_message', 'id': message.id,
                                               'text': message.message_text,
                                               'time': message.created_at,
                                               'edited': message.edited})
                        # in js you should order them by id then if edited is
                        # true get that message and change it to the text that will
                        # be sent here
                    }
                )
            if message_type == 'user_typing_state':
                sent_to = text_data_json['sent_to']
                state = text_data_json['state']  # a boolean variable that true means is typing and false mean is not
                await self.channel_layer.group_send(
                    f'gamer_{sent_to}', {
                        'type': 'friend_message',
                        'message': json.dumps({'type': 'friend_typing_state',
                                               'sent_from': self.user.username, 'is_typing': state})
                    }

                )

            if message_type == 'friend_request':
                print(text_data_json)
                sent_from = text_data_json['sent_from']
                sent_to = text_data_json['sent_to']
                friend_request = await self.create_friend_request(sent_from, sent_to)
                print(sent_to, sent_from)
                await self.channel_layer.group_send(
                    f'gamer_{sent_to}',
                    {
                        'type': 'friend.request',
                        'message': json.dumps({'type': 'friend_request', 'sent_from': sent_from,
                                               'friend_request_id': friend_request.id})
                    }
                )
            if message_type == 'friend_request_accept':
                sent_from = text_data_json['sent_from']
                sent_to = text_data_json['sent_to']
                friend_request_id = text_data_json['friend_request_id']
                this_user, friend = await self.create_friend_delete_request(sent_from=sent_from,
                                                                            friend_request_id=friend_request_id)
                print(friend.id, this_user.id)
                for i in [sent_to, sent_from]:
                    await self.channel_layer.group_send(
                        f'gamer_{i}',
                        {
                            'type': 'friend.request',
                            'message': json.dumps({'type': 'friend_request_accepted',

                                                   'friend': sent_to if i == sent_from else sent_from})
                        }
                    )
            if message_type == 'friend_request_reject':
                friend_request_id = text_data_json['friend_request_id']
                await self.reject_friend_request(friend_request_id)
            if message_type == ['get_friend_requests']:
                friend_requests = await self.get_friends()
                requests_list = []
                for request in friend_requests:
                    requests_list.append(request.sent_from.username)
                await self.send({
                    'type': 'websocket.send',
                    'message': json.dumps({'type': 'receive_friend_requests', 'friends': requests_list})
                })
            # PARTY RELATED MESSAGE TYPE

            if message_type == 'create_party':
                party = await self.create_party()
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'type': 'party_created', 'party_code': party.party_code})
                })
            if message_type == 'remove_friend':
                friend_username = text_data_json['friend_username']
                await self.remove_friend(friend_username)
            # Matchmaking
            if message_type == 'find_a_match':
                game_name = text_data_json['game_name']

            # if await self.is_game_registered(game_name):
                print('Game is registered!...')
                self.user_match_making = await self.create_match_making_or_start_playing(game=game_name)

                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'type': 'match_making_started',
                                        'started_at': str(self.user_match_making.created_at),
                                        'is_searching': self.user_match_making.is_searching})
                })


            if message_type == 'join_the_match':
                match_id = text_data_json['match_id']
                match = Match.objects.get(id=match_id)
                match.add_player(username=self.user.username)

            if message_type == 'cancel_matchmaking':
                print('cancel_matchmaking')
                await self.cancel_matchmaking()

    async def friend_request(self, event):

        print('friend handler send this', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['message']
        })

    async def friend_message(self, event):
        await self.send({
            'type': 'websocket.send',
            'text': event['message']
        })

    async def match_making(self, event):
        match_found = event.get('match_found', None)
        if match_found:
            print('yes and task_cancel_id is:', self.user_match_making.task_cancel_id)
            task = AsyncResult(id=self.user_match_making.task_cancel_id, app=app)
            task.revoke()
        await self.send({
            'type': 'websocket.send',
            'text': event['message']
        })

    @database_sync_to_async
    def friend_send_message(self, sent_to, text):

        return Message.objects.create(sent_from=self.user, sent_to=sent_to, message_text=text)

    @database_sync_to_async
    def edit_message(self, new_text, pk, sent_to):
        try:
            message = Message.objects.get(id=pk)
            if message.sent_from == self.user and message.sent_to.username == sent_to:
                message.message_text = new_text
                message.edited = True
                message.save()
            return message
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist

    @database_sync_to_async
    def create_friend_request(self, sent_from, sent_to):
        try:
            sent_from_user = CustomUser.objects.get(username=sent_from)
            sent_to_user = CustomUser.objects.get(username=sent_to)
            return FriendRequest.objects.create(sent_from=sent_from_user, sent_to=sent_to_user)
        except CustomUser.DoesNotExist as exc:
            raise exc

    @database_sync_to_async
    def create_friend_delete_request(self, sent_from, friend_request_id):
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id)

            friend_request.delete()
            friend = CustomUser.objects.get(username=sent_from)
            self.user.profile.friends.add(friend.profile)
            friend.profile.friends.add(self.user.profile)

            return self.user, friend
        except FriendRequest.DoesNotExist or CustomUser.DoesNotExist as exc:
            raise exc

    @database_sync_to_async
    def reject_friend_request(self, friend_request_id):
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id)
            friend_request.delete()
        except FriendRequest.DoesNotExist as exc:
            raise exc

    @database_sync_to_async
    def get_friends(self):
        return FriendRequest.objects.filter(sent_to=self.user).order_by('-created_at')

    @database_sync_to_async
    def create_party(self):
        try:
            party = Party.objects.create(party_leader=self.user)
        except IntegrityError or Exception:
            party = Party.objects.get(party_leader=self.user)
        return party

    @database_sync_to_async
    def remove_friend(self, friend_username):
        try:
            friend = CustomUser.objects.get(username=friend_username)
            # friend_objects = Friend.objects.filter(Q(user=self.user, friend=friend) | Q(user=friend, friend=self.user))
            # for object in friend_objects:
            #     object.delete()
            self.user.profile.friends.remove(friend.profile)


        except ObjectDoesNotExist as exc:
            raise exc

    @database_sync_to_async
    def set_user_online(self):
        self.user.profile.is_online = True
        self.user.profile.save()

    @database_sync_to_async
    def set_user_offline(self):
        self.user.profile.is_online = False
        self.user.profile.save()

    @database_sync_to_async
    def is_game_registered(self, game_name):
        try:
            game = UserGameRegister.objects.get(user=self.user, game_name=game_name)
            return True
        except ObjectDoesNotExist:
            return False

    @database_sync_to_async
    def create_match_making_or_start_playing(self, game):
        print('Gets in the function')
        matchmaking_task_id = start_matchmaking.apply_async([self.user.username, game],
                                                            expires=900).id
        cancel_matchmaking_id = cancel_matchmaking.apply_async([self.user.username,
                                                                matchmaking_task_id
                                                                ], countdown=900).id


        self.cancel_match_signature = manually_cancel.signature(args=[self.user.username,
                                                                      cancel_matchmaking_id,
                                                                      matchmaking_task_id])

        return UserMatchMakingStatus.objects.create(user=self.user, game=game,
                                                    task_start_id=matchmaking_task_id,
                                                    task_cancel_id=cancel_matchmaking_id,
                                                    is_searching=True)

    @database_sync_to_async
    def cancel_matchmaking(self):
        task = self.cancel_match_signature.delay()
        print(task)

        self.user_match_making.delete()

    # class TestConsumer(AsyncConsumer):
    #     async def websocket_connect(self, event):
    #         self.user = self.scope['user']
    #         print(self.user.username)
    #         print(self.channel_name)
    #         self.group_name = 'gamer_{}'.format(self.user.username)
    #
    #         await self.channel_layer.group_add(
    #             self.group_name,
    #             self.channel_name
    #         )
    #         await self.send({
    #             'type': 'websocket.accept'
    #         })
    #         bytes_array = await self.get_image()
    #
    #         await self.send({
    #             'type': 'websocket.send',
    #             # 'text': json.dumps('bitch'),
    #             'bytes': bytes_array
    #         })
    #
    #     async def websocket_disconnect(self, code):
    #         await self.channel_layer.group_discard(
    #             self.group_name,
    #             self.channel_name
    #         )
    #         raise StopConsumer
    #
    #     async def websocket_receive(self, event):
    #         pass
    #         text_data = event.get('text', None)
    #         bytes_data = event.get('bytes', None)
    #
    #         if text_data:
    #             text_data_json = json.loads(text_data)
    #
    #             await self.channel_layer.group_send(
    #                 self.group_name,
    #                 {
    #                     'type': 'chat_message',
    #                     'message': json.dumps({'text': text_data_json['text']})
    #
    #                 })
    #
    #     async def chat_message(self, event):
    #         await self.send({
    #             'type': 'websocket.send',
    #             'text': event['message'],
    #             'bytes': event['bytes']
    #         })
    #
    #     @database_sync_to_async
    #     def get_image(self):
    #         print(self.user.profile.profile_pic.url)
    #         image = Image.open(self.user.profile.profile_pic)
    #         bytes_array = BytesIO()
    #         image.save(bytes_array, format=image.format)
    #         return bytes_array.getvalue()

    # class MainConsumer(AsyncConsumer):
    #     async def websocket_connect(self, event):
    #         self.user = self.scope['user']
    #         self.group_name = f'gamer_{self.user.username}'
    #
    #         await self.channel_layer.group_add(
    #             self.group_name,
    #             self.channel_name
    #         )
    #
    #         await self.send({
    #             'type': 'websocket.accept',
    #
    #         })
    #
    #     async def websocket_disconnect(self, code):
    #         self.channel_layer.group_discard(
    #             self.group_name,
    #             self.channel_name
    #         )
    #         raise StopConsumer
    #
    #     async def websocket_receive(self, event):
    #         text_data = event.get('text', None)
    #
    #         if text_data:
    #             text_data_json = json.loads(text_data)
    #             message_type = text_data_json['type']
    #
    #             if message_type == 'friend_message':
    #                 sent_to = text_data_json['sent_to']
    #                 await self.friend_send_message(sent_to)
    #                 await self.channel_layer.group_send(
    #                     f'gamer_{sent_to}', {
    #                         'type': 'friend_message',
    #                         'message': json.dumps({'type': 'friend_message', 'sent_from': self.user.username}),
    #                         'user_channel_layer': self.channel_name
    #                     }
    #                 )
    #
    #             if message_type == 'friend_request':
    #                 print(text_data_json)
    #                 sent_from = text_data_json['sent_from']
    #                 sent_to = text_data_json['sent_to']
    #                 friend_request = await self.create_friend_request(sent_from, sent_to)
    #                 print(sent_to, sent_from)
    #                 await self.channel_layer.group_send(
    #                     f'gamer_{sent_to}',
    #                     {
    #                         'type': 'friend.request',
    #                         'message': json.dumps({'type': 'friend_request', 'sent_from': sent_from,
    #                                                'friend_request_id': friend_request.id})
    #                     }
    #                 )
    #             if message_type == 'friend_request_accept':
    #                 sent_from = text_data_json['sent_from']
    #                 sent_to = text_data_json['sent_to']
    #                 friend_request_id = text_data_json['friend_request_id']
    #                 friend, this_user = await self.create_friend_delete_request(sent_from=sent_from,
    #                                                                             friend_request_id=friend_request_id)
    #                 print(friend.id, this_user.id)
    #                 for i in [sent_to, sent_from]:
    #                     await self.channel_layer.group_send(
    #                         f'gamer_{i}',
    #                         {
    #                             'type': 'friend.request',
    #                             'message': json.dumps({'type': 'friend_request_accepted',
    #
    #                                                    'friend': sent_to if i == sent_from else sent_from})
    #                         }
    #                     )
    #             if message_type == 'friend_request_reject':
    #                 friend_request_id = text_data_json['friend_request_id']
    #                 await self.reject_friend_request(friend_request_id)
    #             if message_type == ['get_friend_requests']:
    #                 friend_requests = await self.get_friends()
    #                 requests_list = []
    #                 for request in friend_requests:
    #                     requests_list.append(request.sent_from.username)
    #                 await self.send({
    #                     'type': 'websocket.send',
    #                     'message': json.dumps({'type': 'receive_friend_requests', 'friends': requests_list})
    #                 })
    #             if message_type == 'create_party':
    #                 party = await self.create_party()
    #                 await self.send({
    #                     'type': 'websocket.send',
    #                     'text': json.dumps({'type': 'party_created', 'party_code': party.party_code})
    #                 })
    #
    #     async def friend_request(self, event):
    #         print('friend handler send this', event)
    #         await self.send({
    #             'type': 'websocket.send',
    #             'text': event['message']
    #         })
    #
    #     async def friend_message(self, event):
    #         pass
    #
    #     @database_sync_to_async
    #     def friend_send_message(self, sent_to):
    #         try:
    #
    #             message = Message.objects.create(sent_from=self.user, sent_to=sent_to)
    #         except Message.DoesNotExist as exc:
    #             raise exc
    #
    #     @database_sync_to_async
    #     def create_friend_request(self, sent_from, sent_to):
    #         try:
    #             sent_from_user = CustomUser.objects.get(username=sent_from)
    #             sent_to_user = CustomUser.objects.get(username=sent_to)
    #             return FriendRequest.objects.create(sent_from=sent_from_user, sent_to=sent_to_user)
    #         except CustomUser.DoesNotExist as exc:
    #             raise exc
    #
    #     @database_sync_to_async
    #     def create_friend_delete_request(self, sent_from, friend_request_id):
    #         try:
    #             friend_request = FriendRequest.objects.get(id=friend_request_id)
    #
    #             friend_request.delete()
    #             friend = CustomUser.objects.get(username=sent_from)
    #             friend_model1 = Friend.objects.create(user_id=self.user.id, friend=friend)
    #             friend_model2 = Friend.objects.create(user_id=friend.id, friend=self.user)
    #
    #             return friend_model1.friend, friend_model2.friend
    #         except FriendRequest.DoesNotExist or CustomUser.DoesNotExist as exc:
    #             raise exc
    #
    #     @database_sync_to_async
    #     def reject_friend_request(self, friend_request_id):
    #         try:
    #             friend_request = FriendRequest.objects.get(id=friend_request_id)
    #             friend_request.delete()
    #         except FriendRequest.DoesNotExist as exc:
    #             raise exc
    #
    #     @database_sync_to_async
    #     def get_friends(self):
    #         return FriendRequest.objects.filter(sent_to=self.user).order_by('-created_at')
    #
    #     @database_sync_to_async
    #     def create_party(self):
    #         party = Party.objects.create(party_leader=self.user)
    #         return party