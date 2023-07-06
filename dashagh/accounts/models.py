from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, AbstractUser
from matches_and_ranks.models import PartyMember, Organizer


# class CustomUserManager(BaseUserManager):
#     def create_user(self, username, email, password, key_expires):
#         if not email:
#             raise ValueError('Users must have an email address')
#
#         if not username:
#             raise ValueError("users must have a username")
#
#         if not password:
#             raise ValueError('users must have password')
#
#         user = self.model(
#             username=username,
#             email=self.normalize_email(email),
#             key_expires=key_expires,
#         )
#
#         user.set_password(password)
#         user.save(using=self._db)
#         return user


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(max_length=40, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    # USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    profile_pic = models.ImageField(null=True, blank=True)
    friends = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return self.user.username + 'profile'

    def is_in_party(self):

        party_member = PartyMember.objects.filter(user=self.user).first()
        if party_member:
            return True
        else:
            return False
class Follower(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, null=True)
    followers = models.ManyToManyField('self', blank=True)



# class Friend(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_friend_model')
#     friend = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='friend_friend_model')
#
#


class FriendRequest(models.Model):
    sent_to = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_to_friend_request_model')
    sent_from = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_from_friend_request_model')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{} sent to {}'.format(self.sent_from, self.sent_to)


class ShopItem(models.Model):
    name = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    price = models.FloatField(default=0)