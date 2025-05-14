# Import Django's models module to define database models
from django.db import models

# Import AbstractUser to customize Django’s built-in User model
from django.contrib.auth.models import AbstractUser
from django.conf import settings


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




class Tour(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='tours/')
    duration_days = models.PositiveIntegerField()
    status = models.CharField(max_length=50)
    description = models.TextField()  # ✅ renamed from 'review' to 'description'
    created_at = models.DateTimeField(auto_now_add=True)  


class Booking(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('confirmed', 'Confirmed'), ('pending', 'Pending'), ('cancelled', 'Cancelled')])

class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50)

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)