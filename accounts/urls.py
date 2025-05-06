# Import the 'path' function which is used to define URL patterns.
from django.urls import path

# Import the views module from the current directory ('.') to connect URLs to view functions.
from . import views

# Define a list of URL patterns for the app.
urlpatterns = [
    # When the user visits /register/, Django will call the register_view function in views.py.
    # The 'name' parameter allows you to refer to this URL in templates using {% url 'register' %}.
    path('register/', views.register_view, name='register'),

    # When the user visits /login/, Django will call the login_view function.
    # You can reference this URL with {% url 'login' %}.
    path('login/', views.login_view, name='login'),

    # When the user visits /logout/, Django will call the logout_view function.
    # Use {% url 'logout' %} in templates to link to this URL.
    path('logout/', views.logout_view, name='logout'),
]
