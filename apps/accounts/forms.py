from django import forms
from django.contrib.auth.forms import AuthenticationForm

from apps.accounts.models import User


class HobbitAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        error_messages={'required': 'Please enter an email address you dribbling buffoon ;)'},
    )
    password = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput,
        error_messages={'required': "If you don't have a password use the forgotten password link. If you do, just enter it, Einstein."},
    )

    error_messages = {
        'invalid_login': "We don't recognise this password. Please try again or use the forgotten password link.",
        'no_cookies': "Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in.",
        'inactive': "This account is inactive.",
    }

    def clean_username(self):
        email = self.cleaned_data.get('username')
        user_count = User.objects.filter(email=email).count()
        if user_count == 0:
            raise forms.ValidationError("We can't find an account for this email address. Please check and try again.")
        return email
