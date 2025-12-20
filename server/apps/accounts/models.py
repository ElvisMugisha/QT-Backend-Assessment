from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Minimal custom user model.
    Authenticated via mTLS (CN=email), so no password required.
    """
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    # State fields requested by spec
    # lastSeen: nanoseconds since epoch
    last_seen_ns = models.BigIntegerField(default=0)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.IntegerField(default=0)

    # Required for custom user model
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
