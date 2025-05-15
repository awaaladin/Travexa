# Import Django's forms library to create form classes
from django import forms

# Import built-in user creation and authentication forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Import the custom user model you defined in models.py
from .models import CustomUser


# Define a form for user registration based on Django's built-in UserCreationForm
class CustomUserCreationForm(UserCreationForm):
    # Add specific field customizations
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # Meta class provides metadata to specify which model the form is related to
    class Meta:
        # This form will use the CustomUser model (instead of Django's default User model)
        model = CustomUser

        # These are the fields from the model to show in the form
        # password1 and password2 are for password and password confirmation
        fields = ['username', 'email', 'role', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


# Define a custom login form based on Django's built-in AuthenticationForm
class CustomLoginForm(AuthenticationForm):
    # Override the default username field to add Bootstrap styling
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})  # Apply Bootstrap class
    )

    # Override the default password field to use a password input with Bootstrap styling
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})  # Apply Bootstrap class
    )