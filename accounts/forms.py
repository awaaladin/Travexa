# Import Django's forms library to create form classes
from django import forms

# Import built-in user creation and authentication forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Import the custom user model you defined in models.py
from .models import CustomUser


# Define a form for user registration based on Django’s built-in UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    # Meta class provides metadata to specify which model the form is related to
    class Meta:
        # This form will use the CustomUser model (instead of Django's default User model)
        model = CustomUser

        # These are the fields from the model to show in the form
        # password1 and password2 are for password and password confirmation
        fields = ['username', 'email', 'role', 'password1', 'password2']


# Define a custom login form based on Django’s built-in AuthenticationForm
class CustomLoginForm(AuthenticationForm):
    # Override the default username field to add Bootstrap styling
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})  # Apply Bootstrap class
    )

    # Override the default password field to use a password input with Bootstrap styling
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})  # Apply Bootstrap class
    )


"""You’re extending built-in Django forms to customize how they look and which fields they include.

UserCreationForm helps with registration and AuthenticationForm helps with login.

Bootstrap form-control classes are added to make the forms look cleaner and consistent with Bootstrap UI styling."""