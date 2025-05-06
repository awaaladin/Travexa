# Import Django's models module to define database models
from django.db import models

# Import AbstractUser to customize Django’s built-in User model
from django.contrib.auth.models import AbstractUser


# Define a custom user model by extending Django’s default AbstractUser
class CustomUser(AbstractUser):
    # Define a set of possible roles users can have in the system
    ROLE_CHOICES = (
        ('customer', 'Customer'),  # Role for normal users booking tours
        ('guide', 'Guide'),        # Role for people offering tours
        ('admin', 'Admin'),        # Role for admin-level users (if needed)
    )

    # Add a new field called 'role' to the user model
    # This field will store one of the predefined roles above
    role = models.CharField(
        max_length=10,             # Max length of the text in this field
        choices=ROLE_CHOICES,      # Restrict values to only those in ROLE_CHOICES
        default='customer'         # Set the default role to 'customer' if none is selected
    )


"""This code customizes the user model to include a role field.

In Django, customizing AbstractUser is a common way to add extra fields to the default user system.

The role field allows your app to differentiate between customers, tour guides, and admins."""