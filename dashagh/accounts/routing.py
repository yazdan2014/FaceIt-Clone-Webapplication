from django.urls import path
from accounts.consumers.main_consumer import *
from accounts.consumers.party_consumer import *

websocket_urlpatterns = [
    # path('ws/testing/', TestConsumer),
    path('ws/main/', MainConsumer),
    path('ws/party_chat/<str:party_code>/', PartyConsumer),

]
