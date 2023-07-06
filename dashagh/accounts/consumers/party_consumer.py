from channels.consumer import AsyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
from channels.db import database_sync_to_async
import json
from asgiref.sync import sync_to_async
from accounts.models import CustomUser, Profile, FriendRequest
from matches_and_ranks.models import Party, PartyMember, PartyMessage
from news.models import Message
from django.db.models import Q
from asgiref.sync import sync_to_async, async_to_sync
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import random
# converting images to bytes array
from io import BytesIO
from PIL import Image
from autobahn.exception import Disconnected
import time
import threading




class PartyConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        self.user = self.scope['user']
        self.party_code = self.scope['url_route']['kwargs']['party_code']
        self.party_group_name = f'party_{self.party_code}'
        self.party = await self.get_party()
        print(self.user.username)
        print(self.channel_name)
        if self.party:
            if not await self.is_party_full() and (await self.is_in_same_party() or not await self.has_party()):
                await self.channel_layer.group_add(
                    self.party_group_name,
                    self.channel_name
                )
                await self.send({
                    'type': 'websocket.accept',
                })
                await self.channel_layer.group_send(
                    self.party_group_name,
                    {
                        'type': 'party_message',
                        'message': json.dumps(
                            {'type': 'party_joined', 'who_joined': self.user.username, 'party_code': self.party_code}),
                        'user_channel_name': self.channel_name,
                    }
                )

                await self.create_member()

                party_members_info = await self.get_members_info()
                print(party_members_info)
                await self.channel_layer.group_send(self.party_group_name,
                                                    {
                                                        'type': 'party_message',
                                                        'message': json.dumps(
                                                            {'type': 'party_members', 'info': party_members_info,
                                                             }),

                                                    })



        else:
            raise StopConsumer

    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard(
            self.party_group_name,
            self.channel_name
        )
        raise StopConsumer

    async def websocket_receive(self, event):
        text_data = event.get('text', None)
        bytes_data = event.get('bytes', None)
        self.party = await self.get_party()
        if text_data:
            text_data_json = json.loads(text_data)

            message_type = text_data_json['type']

            print(message_type == 'party_send_message')

            print(message_type)

            if message_type == 'party_invite_send':

                sent_to = text_data_json['sent_to']
                friend = await self.get_friend(sent_to)
                print(friend)
                if friend:
                    if not await sync_to_async(friend.is_in_party)():
                        if not await self.is_party_full():
                            await self.channel_layer.group_send(
                                f'gamer_{sent_to}',
                                {
                                    'type': 'friend_request',
                                    'message': json.dumps({'type': 'party_invite_receive',
                                                           'party_code': self.party.party_code,
                                                           'from': self.user.username}),

                                }
                            )

            if message_type == 'leave_party':

                self.party = await self.get_party()
                print(text_data_json)
                await self.member_leave()
                if await self.is_party_leader():
                    # await self.channel_layer.group_send(
                    #     self.party_group_name,
                    #     {
                    #         'type': 'party_message',
                    #         # this is for when party leader has left
                    #         'message': json.dumps({'type': 'delete_party'}),
                    #         'user_channel_name': self.channel_name,
                    #     }
                    # )
                    # await self.delete_party_model()
                    await self.change_party_leader()

                party_members_info = await self.get_members_info()
                await self.channel_layer.group_send(self.party_group_name,
                                                    {
                                                        'type': 'party_message',
                                                        'message': json.dumps(
                                                            {'type': 'party_members', 'info': party_members_info,
                                                             }),
                                                        'user_channel_name': self.channel_name,
                                                    })

                await self.channel_layer.group_send(self.party_group_name,
                                                    {
                                                        'type': 'party_message',
                                                        'message': json.dumps(
                                                            {'type': 'party_left', 'who_left': self.user.username}),
                                                        'user_channel_name': self.channel_name,
                                                    })
                await self.send({"type": "websocket.close", "code": 1000})

            if message_type == 'party_kick':
                if await self.is_party_leader():
                    kicked_user = text_data_json['kicked_user']
                    await self.channel_layer.group_send(self.party_group_name, {
                        'type': 'kick_member',
                        'message': json.dumps(
                            {'type': 'kicked_out', 'from': f'{self.user.username}\'s party'}),
                        'kicked_user': kicked_user
                    })

            if message_type == 'promote':
                self.party = await self.get_party()
                new_party_leader = text_data_json['new_party_leader']
                await self.new_party_leader()
                party_members_info = await self.get_members_info()
                await self.channel_layer.group_send(self.party_group_name, {
                    'type': 'party_message',
                    'message': json.dumps(
                        {'type': 'party_members', 'info': party_members_info,
                         }),

                })
                await self.channel_layer.group_send(self.party_group_name, {
                    'type': 'party_message',
                    'message': json.dumps({'type': 'leader_changed', 'new_leader': new_party_leader})
                })
            if message_type == 'party_send_message':
                print(text_data_json)
                # This is the same as the fucking friend messages you
                # send that you wanna edit it or not the I do the rest
                # The only difference is that we don't have a sent_to
                edited = text_data_json['edited']  # default false
                print(edited)
                text = text_data_json['text']
                print("This one ", (('<' or '\'') in text))
                if ('<' not in text) and ('>' not in text) and ('\'' not in text) and ('\"' not in text):
                    if edited:
                        message_id = text_data_json['message_id']

                        party_message = await self.edit_party_message(pk=message_id, new_text=text)
                    else:


                        party_message = await self.create_party_message(text=text)

                    await self.channel_layer.group_send(
                        self.party_group_name, {
                            'type': 'party_message',
                            'message': json.dumps({'type': 'party_message', 'id': int(party_message.id),
                                                   'sent_from': party_message.sent_from.username,
                                                   'text': party_message.message_text,
                                                   'time': str(party_message.created_at),
                                                   'edited': party_message.edited,

                                                   }),

                            # and remember that you should edit or add message for the user itself because it will not be sent to himself will discuss it if you want but the reason is mainly about that its the same system that i used for friend_message
                            # in js you should order them by id then if edited is
                            # true get that message and change it to the text that will
                            # be sent here
                        }
                    )
            if message_type == 'user_typing_state':
                state = text_data_json['state']
                # a boolean variable that true means is typing and false mean is not
                await self.channel_layer.group_send(
                    self.party_group_name, {
                        'type': 'party_message',
                        'message': json.dumps({'type': 'friend_typing_state',
                                               'sent_from': self.user.username, 'is_typing': state}),
                        'user_channel_name': self.channel_name
                    }

                )

    async def party_message(self, event):
        user_channel_name = event.get('user_channel_name', None)
        print(event)

        if user_channel_name != self.channel_name:
            await self.send({
                'type': 'websocket.send',
                'text': event['message']
            })

    @database_sync_to_async
    def get_party(self):
        try:
            return Party.objects.get(party_code=self.party_code)
        except Party.DoesNotExist:
            return None

    @database_sync_to_async
    def member_leave(self):

        member = self.party.partymember_set.get(user=self.user)
        member.delete()

    @database_sync_to_async
    def get_members_info(self):

        party_members = self.party.partymember_set.all()
        print(party_members)
        party_info = []
        for member in party_members:
            party_info.append({'username': member.user.username,
                               'profile_pic_url': member.user.profile.profile_pic.url,
                               'is_party_leader': True if member.user == self.party.party_leader else False
                               })

        return party_info

    @database_sync_to_async
    def delete_party_model(self):
        party = Party.objects.get(party_code=self.party_code)
        party.delete()

    @database_sync_to_async
    def create_member(self):
        try:
            return PartyMember.objects.create(user=self.user, party=self.party)
        except IntegrityError:
            return None

    @database_sync_to_async
    def get_friend(self, sent_to):
        try:
            friend = CustomUser.objects.get(username=sent_to)
            friend_profile = self.user.profile.friends.filter(user=friend).first()
            print(friend_profile)
            return friend_profile
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def change_party_leader(self):

        party_members = list(self.party.partymember_set.all())
        print(len(party_members))
        if len(party_members):

            random_member = random.choice(party_members)
            self.party.party_leader = random_member.user
            self.party.save()
        else:
            self.party.delete()

    @database_sync_to_async
    def is_party_leader(self):
        if self.user == self.party.party_leader:
            return True
        else:
            return False

    async def kick_member(self, event):
        kicked_user = event['kicked_user']
        print(self.user.username == kicked_user)

        print(kicked_user == self.user.username)
        if self.user.username == kicked_user:
            await self.member_leave()
            await self.send({
                'type': 'websocket.send',
                'text': json.dumps({'type': 'kicked_out'})
            })
            party_members_info = await self.get_members_info()
            await self.channel_layer.group_send(self.party_group_name, {
                'type': 'party_message',
                'message': json.dumps(
                    {'type': 'party_members', 'info': party_members_info,
                     }),
            })
            await self.send({'type': 'websocket.close', 'code': 1000})


        else:
            await self.send({'type': 'websocket.send', 'text': event['message']})

    @database_sync_to_async
    def new_party_leader(self, new_party_leader):
        party_leader = CustomUser.objects.get(username=new_party_leader)
        self.party.party_leader = party_leader
        self.party.save()

    @database_sync_to_async
    def is_party_full(self):
        if self.party.partymember_set.all().count() == 5:
            return True
        elif self.party.partymember_set.all().count() > 5:
            raise PartyFullError('Party is full ')
        else:
            return False

    @database_sync_to_async
    def create_party_message(self, text):

        party_message = PartyMessage.objects.create(party=self.party,
                                                    sent_from=self.user, message_text=text)
        return party_message

    @database_sync_to_async
    def edit_party_message(self, pk, new_text):
        try:
            party_message = PartyMessage.objects.get(id=pk)
            if party_message.sent_from == self.user:
                party_message.message_text = new_text
                party_message.edited = True
                party_message.save()
            return party_message

        except ObjectDoesNotExist as exc:
            raise exc

    @database_sync_to_async
    def is_in_same_party(self):
        party_member = PartyMember.objects.filter(party=self.party, user=self.user).first()
        if party_member:
            return True
        else:
            return False

    @database_sync_to_async
    def has_party(self):
        try:
            party_member = PartyMember.objects.get(user=self.user)
            return True
        except ObjectDoesNotExist:
            return False


class PartyFullError(Exception):
    pass
