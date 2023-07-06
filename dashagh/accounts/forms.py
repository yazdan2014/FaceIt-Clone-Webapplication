from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, ShopItem
from django.forms import forms

class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password1', 'password2')
        labels = ['Email:', 'Username:', 'Password:', 'Password Confirmation:']

class ShopItemsForm(forms.Form):
    class Meta:
        model = ShopItem
        fields = ['name', 'details', 'price']