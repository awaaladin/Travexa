# Import necessary modules from Django and other libraries.
from django.shortcuts import render, redirect  # To render templates and redirect users to different pages
from django.contrib.auth import authenticate, login, logout  # For handling authentication-related operations
from .forms import CustomUserCreationForm, CustomLoginForm  # Import the custom forms for registration and login
import logging  # For logging purposes, useful for debugging
from django.contrib import messages  # For displaying success or error messages to users
from accounts.models import CustomUser, Tour, Booking, Payment
from django.db.models import Count, Sum


from django.shortcuts import render
from django.db.models import Count, Sum
from accounts.models import CustomUser, Tour, Booking, Payment, Review

def dashboard(request):
    total_users = CustomUser.objects.count()
    tourist_count = CustomUser.objects.filter(role='customer').count()
    guide_count = CustomUser.objects.filter(role='guide').count()
    admin_count = CustomUser.objects.filter(role='admin').count()
    
    active_tours = Tour.objects.filter(status='active').count()
    cancelled_tours = Tour.objects.filter(status='cancelled').count()
    pending_tours = Tour.objects.filter(status='pending').order_by('-id')[:5]
    
    total_bookings = Booking.objects.count()
    confirmed_bookings = Booking.objects.filter(status='confirmed').count()
    pending_bookings = Booking.objects.filter(status='pending').count()
    cancelled_bookings = Booking.objects.filter(status='cancelled').count()

    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_reviews = Review.objects.count()

    # Recent records
    recent_bookings = Booking.objects.select_related('user', 'tour').order_by('-date')[:5]
    recent_tours = Tour.objects.order_by('-id')[:4]

    # For charts
    revenue_chart = [15000, 22000, 19000, 28000, 32000]
    bookings_chart = [120, 160, 145, 182, 210]

    user_roles = {
        'tourists': tourist_count,
        'guides': guide_count,
        'admins': admin_count,
    }

    context = {
        'total_users': total_users,
        'tourist_count': tourist_count,
        'guide_count': guide_count,
        'admin_count': admin_count,
        'active_tours': active_tours,
        'pending_tours': pending_tours,
        'cancelled_tours': cancelled_tours,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': total_revenue,
        'total_reviews': total_reviews,
        'recent_bookings': recent_bookings,
        'recent_tours': recent_tours,
        'revenue_chart': revenue_chart,
        'bookings_chart': bookings_chart,
        'user_roles': user_roles,
    }

    return render(request, 'accounts/dashboard.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('dashboard')  # change to your desired redirect
        else:
            messages.error(request, "Registration failed. Please fix the errors.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')  # change to your desired redirect
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')

def user_list(request):
    return render(request, 'accounts/users.html')

def tour_list(request):
    return render(request, 'accounts/tours.html')

def booking_list(request):
    return render(request, 'accounts/bookings.html')

def payment_list(request):
    return render(request, 'accounts/payments.html')

def review_list(request):
    return render(request, 'accounts/reviews.html')

def report_view(request):
    return render(request, 'accounts/reports.html')

def settings_view(request):
    return render(request, 'accounts/settings.html')