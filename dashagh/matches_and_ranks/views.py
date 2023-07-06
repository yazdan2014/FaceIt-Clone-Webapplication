from django.shortcuts import render
from django.http import HttpResponse
from matches_and_ranks.models import PartyMember, Party
from .models import Rank
from accounts.models import FriendRequest
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required()
def home_view(request, *args, **kwargs):
    friends = request.user.profile.friends.all()

    if request.user.is_authenticated:
        friend_requests = FriendRequest.objects.filter(sent_to=request.user)
        friend_requests_sent = []
        for friend_request in friend_requests:
            friend_requests_sent.append(friend_request.sent_to.username)
        new_friend_requests = len(friend_requests_sent)

        party_member = PartyMember.objects.filter(user=request.user).first()
        party = None
        rank = request.user.rank
        if party_member:
            party = party_member.party
        dictionary = {'rank': request.user.rank,
                      'new_friend_requests': new_friend_requests, 'friends': friends}
        if party:
            dictionary['party'] = party
        return render(request, 'news/Home.html', dictionary)
    else:
        return HttpResponse('Fucker you should login first')


@login_required
def play_view(request, *args, **kwargs):
    friend_requests = FriendRequest.objects.filter(sent_to=request.user)
    friend_requests_sent = []
    for friend_request in friend_requests:
        friend_requests_sent.append(friend_request.sent_to.username)
    new_friend_requests = len(friend_requests_sent)

    rank = request.user.rank
    return render(request, 'matches_and_ranks/play.html', {"rank": rank,
                                                           'new_friend_requests': new_friend_requests
                                                           })
