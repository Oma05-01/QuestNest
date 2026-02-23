from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .manager import UserManager

ROLE_CHOICES = (
    ('tenant', 'Tenant'),
    ('landlord', 'Landlord'),
    ('agent', 'Agent'),
    ('admin', 'Admin'),
)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # only email + password required

    objects = UserManager()

    def __str__(self):
        return self.email