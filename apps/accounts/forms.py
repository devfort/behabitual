from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm

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


class HobbitPasswordResetNotStupidForm(PasswordResetForm):
    error_messages = {
        'unknown': "That email address doesn't have an associated "
                     "user account. Are you sure you've registered?",
        'inactive': "You haven't confirmed your email address so we cannot reset your password. Please get in touch.",
    }
    
    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        UserModel = get_user_model()
        email = self.cleaned_data["email"]
        self.users_cache = UserModel._default_manager.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if not any(user.is_active for user in self.users_cache):
            # none of the filtered users are active
            raise forms.ValidationError(self.error_messages['inactive'])
        return email
    