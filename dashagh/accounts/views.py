from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
from django.shortcuts import HttpResponse
from django.views.generic import CreateView, FormView
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser, Profile, ShopItem, FriendRequest
from .forms import SignUpForm
from matches_and_ranks.models import Rank
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
import json
from matches_and_ranks.models import Party, PartyMember, PartyMessage
from django.contrib.auth.decorators import login_required


# def login_user(request):
#     if request.method == 'POST':
#         user = authenticate(username='soroush', email='soroush.salari83@icloud.com', password='1')
#         if user is None:
#             return HttpResponse('you\'re not authenticated')
#         return HttpResponse(f'Hello {user.username}')
#
#     return render(request, template_name='accounts/home.html')

def party_chat_messages(request):
    if request.is_ajax and request.method == "GET":
        party_code = request.GET.get("party_code", None)
        try:
            party = Party.objects.get(party_code=party_code)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist

        party_messages = PartyMessage.objects.filter(party=party).order_by("created_at")[:30]

        party_messages_render = []
        for message in party_messages:
            party_messages_render.append({"sent_from": message.sent_from.username, "message_text": message.message_text,
                                          "created_at": message.created_at, "edited": message.edited,
                                          "profile_pic_url": message.sent_from.profile.profile_pic.url,
                                          "message_id": message.id
                                          })
        return JsonResponse(party_messages_render, status=200, safe=False)


@login_required
def shop_view(request):
    friend_requests = FriendRequest.objects.filter(sent_to=request.user)
    friend_requests_sent = []
    for friend_request in friend_requests:
        friend_requests_sent.append(friend_request.sent_to.username)
    new_friend_requests = len(friend_requests_sent)

    shop_items = ShopItem.objects.all()
    party_member = PartyMember.objects.filter(user=request.user).first()
    party = None
    if party_member:
        party = party_member.party
    dictionary = {'rank': request.user.rank, 'shop_items': shop_items,
                  'new_friend_requests': new_friend_requests
                  }
    if party:
        dictionary['party'] = party
        print('there is a party')
    return render(request, 'accounts/Shop.html', dictionary)


def home(request):
    friend_requests = FriendRequest.objects.filter(sent_from=request.user)
    friend_requests_sent = []
    for friend_request in friend_requests:
        friend_requests_sent.append(friend_request.sent_to.username)
    new_friend_requests = len(friend_requests_sent)

    if request.user.is_authenticated is not True:
        return HttpResponse('Fucker you should authenticate first.')
    return render(request, 'accounts/home.html', {'username': mark_safe(json.dumps(request.user.username)),
                                                  'new_friend_requests': new_friend_requests
                                                  })


@login_required
def friends_view(request):
    friend_requests = FriendRequest.objects.filter(sent_from=request.user)
    friend_requests_sent = []
    for friend_request in friend_requests:
        friend_requests_sent.append(friend_request.sent_to.username)
    new_friend_requests = len(friend_requests_sent)

    friend_requests = FriendRequest.objects.filter(sent_to=request.user)
    friends = request.user.profile.friends.all()

    party_member = PartyMember.objects.filter(user=request.user).first()
    party = None
    if party_member:
        party = party_member.party
    dictionary = {'rank': request.user.rank, 'friends': friends, 'friend_requests': friend_requests
                  }
    if party:
        dictionary['party'] = party
    return render(request, 'accounts/friends.html', dictionary)


@login_required
def search_result(request):
    # if 'search_result' in request.POST['kwargs']
    party = None
    if request.method == "POST":
        searched = request.POST['searched']
        friend_requests = FriendRequest.objects.filter(sent_from=request.user)
        friend_requests_sent = []
        for friend_request in friend_requests:
            friend_requests_sent.append(friend_request.sent_to.username)

        new_friend_requests = len(friend_requests_sent)

        friends = request.user.profile.friends.all()
        friends_usernames = []
        for friend in friends:
            friends_usernames.append(friend.user.username)

        users = CustomUser.objects.filter(username__contains=searched)
        return render(request, 'accounts/search_result.html',
                      {'searched': searched, 'users': users, "rank": request.user.rank,
                       "friends_usernames": friends_usernames, "friend_requests_sent": friend_requests_sent,
                       'new_friend_requests': new_friend_requests})
    else:
        return render(request, 'accounts/search_result.html', {"rank": request.user.rank})


class SignUpView(CreateView):
    model = CustomUser
    template_name = 'accounts/register.html'
    success_url = '/accounts/login'
    form_class = SignUpForm

    def form_valid(self, form):
        user = form.instance
        user.save()
        rank = Rank.objects.create(user=user)
        profile = Profile.objects.create(user_id=user.id)

        return super(SignUpView, self).form_valid(form)


class LoginView(FormView):
    model = CustomUser
    template_name = 'accounts/login.html'
    success_url = '/'
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        if user is not None:
            login(self.request, user)

        try:
            rank = Rank.objects.get(user=user)
        except ObjectDoesNotExist:
            Rank.objects.create(user=user)
        try:
            profile = Profile.objects.get(user=user)
        except ObjectDoesNotExist:
            Profile.objects.create(user=user)

        return super(LoginView, self).form_valid(form)


def player_profile(request, username):
    friend_requests = FriendRequest.objects.filter(sent_to=request.user)
    friend_requests_sent = []
    for friend_request in friend_requests:
        friend_requests_sent.append(friend_request.sent_to.username)

    new_friend_requests = len(friend_requests_sent)
    try:
        player = CustomUser.objects.get(username=username)
        return render(request, 'accounts/user_interface.html',
                      {'player_user': player, 'new_friend_requests': new_friend_requests})
    except ObjectDoesNotExist:
        HttpResponse('Go fuck yourself')
