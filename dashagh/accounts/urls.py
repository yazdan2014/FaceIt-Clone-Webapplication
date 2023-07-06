from django.urls import path
from . import views
from accounts.views import party_chat_messages

app_name = 'accounts'

urlpatterns = [
    path('get/ajax/party_messages', party_chat_messages, name='party_chat_messages'),

    path('index/', views.home, name='index'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('searchresult/', views.search_result, name='search-result'),
    path('shop/', views.shop_view, name='shop'),
    path('friends/', views.friends_view, name='friends'),
    path('players/<str:username>/', views.player_profile, name='player_profile'),

]
