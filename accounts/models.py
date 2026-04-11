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

    # 🟢 THE MISSING LINK: Every user must belong to an Org
    # We use a string reference 'organisations.Organisation' to avoid circular imports
    organisation = models.ForeignKey(
        'organisations.Organisation',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # Allow null temporarily for existing users if needed
        blank=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tenant')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']  # Added name here as it's good practice

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"