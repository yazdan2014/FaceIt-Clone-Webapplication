from django.contrib import admin

from .models import Party, PartyMember, Rank, PartyMessage, Match


admin.site.register(Party)
admin.site.register(Match)
admin.site.register(PartyMember)
admin.site.register(Rank)
admin.site.register(PartyMessage)
