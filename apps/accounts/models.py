from django.contrib.auth import models as user_models
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class UserManager(user_models.BaseUserManager):
    """
    Custom user manager because we're using different fields on our User model
    than Django's default User model
    """

    def create_user(self, email=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        email = UserManager.normalize_email(email)
        fields = {
            'is_staff': False,
            'is_active': False,
            'is_superuser': False,
            'email': email,
            'last_login': now,
            'date_joined': now,
        }
        # Allow kwargs to over-write default value for is_active etc. Useful in tests
        fields.update(extra_fields)
        user = self.model(**fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


class User(user_models.AbstractBaseUser, user_models.PermissionsMixin):
    email = models.CharField(max_length=500, unique=True, db_index=True)
    name = models.CharField(max_length=500)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
    	return self.name

    def get_short_name(self):
        return self.name
