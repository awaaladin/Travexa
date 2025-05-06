# Import necessary modules from Django and other libraries.
from django.shortcuts import render, redirect  # To render templates and redirect users to different pages
from django.contrib.auth import authenticate, login, logout  # For handling authentication-related operations
from .forms import CustomUserCreationForm, CustomLoginForm  # Import the custom forms for registration and login
import logging  # For logging purposes, useful for debugging
from django.contrib import messages  # For displaying success or error messages to users

# Initialize a logger instance to record events for debugging purposes.
logger = logging.getLogger(__name__)

# This view handles the user registration process.
def register_view(request):
    if request.method == 'POST':  # If the request method is POST, it means the user is submitting the form.
        form = CustomUserCreationForm(request.POST)  # Create an instance of the registration form with the POST data.
        if form.is_valid():  # If the form is valid (all fields pass validation checks)
            form.save()  # Save the new user to the database
            messages.success(request, 'Registration successful! Please log in.')  # Display a success message to the user

            return redirect('accounts/login')  # Redirect the user to the login page after successful registration
    else:  # If the request method is not POST (i.e., the page is being loaded for the first time)
        form = CustomUserCreationForm()  # Create an empty form for the user to fill out

    return render(request, 'accounts/register.html', {'form': form})  # Render the registration template with the form

# This view handles the user login process.
def login_view(request):
    if request.method == 'POST':  # If the request method is POST, it means the user is submitting the login form.
        form = CustomLoginForm(request, data=request.POST)  # Create an instance of the login form with the POST data.
        if form.is_valid():  # If the form is valid (credentials are correct)
            user = form.get_user()  # Retrieve the user object based on the form data.
            login(request, user)  # Log the user in by storing their session
            return redirect('dashboard')  # Redirect the user to the dashboard (or any other post-login page)
    else:  # If the request method is not POST, it means the page is being loaded for the first time
        form = CustomLoginForm()  # Create an empty login form for the user to fill out
    
    return render(request, 'accounts/login.html', {'form': form})  # Render the login template with the form

# This view handles the user logout process.
def logout_view(request):
    logout(request)  # Log the user out by clearing their session
    return redirect('login')  # Redirect the user to the login page after logging out


"""Imports:

1.render and redirect help render templates and redirect users to other pages.

2.authenticate, login, logout are for handling user authentication (sign-in and sign-out).

3.CustomUserCreationForm and CustomLoginForm are custom forms for user registration and login.

4.logging helps log messages for debugging.

5.messages is used to show success or error messages to the user.

Functions:

1.register_view: Handles the user registration process. It processes the form and saves the user data if valid. It redirects to the login page after successful registration.

2.login_view: Handles the login process. It checks if the form data is valid and logs the user in if so. Then it redirects the user to the dashboard or a post-login page.

3.logout_view: Logs the user out and redirects them to the login page.

Form Handling:

. When a request is POST, it means the user submitted a form, and Django processes the form's data (form.is_valid() checks if the form's input is valid).

. If the form is valid, the appropriate action (saving the user or logging in) happens.

.If the request is not POST (i.e., the page is loaded initially), an empty form is displayed for the user to fill out"""