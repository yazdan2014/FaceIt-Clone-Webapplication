from django.contrib import admin
from .models import CustomUser, Profile, FriendRequest, ShopItem


# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(ShopItem)
admin.site.register(FriendRequest)
