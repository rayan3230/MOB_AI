from django.db import models
from django.contrib.auth.models import AbstractUser


ROLE_CHOICES = (
    ('Employee', 'Employee'),
    ('Supervisor', 'Supervisor'),
    ('Admin', 'Admin'),
)


class CustomUser(AbstractUser):
    user_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    user_name = models.CharField(max_length=150, unique=True , null=False, blank=False)
    user_role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=True, blank=True)
    user_email = models.EmailField(unique=True, null=True, blank=True)
    user_visibility = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.user_code:
            self.user_code = f"U{self.pk}"
            super().save(update_fields=["user_code"])
