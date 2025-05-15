from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import CustomUserCreationForm, CustomLoginForm
from .models import CustomUser, Tour, Booking, Payment, Review
from django.db.models import Sum


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            # if user is not None:
            #     login(request, user)
            #     messages.success(request, f"Registration successful. Welcome {username}!")
            #     return redirect('dashboard')
            if user:
                messages.success(request, "Registration successful. Please log in.")
                return redirect('login')
        else:
            # Print form errors to console for debugging
            print(f"Form errors: {form.errors}")
            messages.error(request, "Registration failed. Please fix the errors.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                # Use explicit URL instead of name to avoid potential issues
                return redirect(reverse('dashboard'))
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Print form errors to console for debugging
            print(f"Form errors: {form.errors}")
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')


@login_required
def dashboard(request):
    # Add debugging information
    print(f"User accessed dashboard: {request.user.username}, authenticated: {request.user.is_authenticated}")
    
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

    recent_bookings = Booking.objects.select_related('user', 'tour').order_by('-date')[:5]
    recent_tours = Tour.objects.order_by('-id')[:4]

    context = {
        'total_users': total_users,
        'tourist_count': tourist_count,
        'guide_count': guide_count,
        'admin_count': admin_count,
        'active_tours': active_tours,
        'cancelled_tours': cancelled_tours,
        'pending_tours': pending_tours,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_revenue': total_revenue,
        'total_reviews': total_reviews,
        'recent_bookings': recent_bookings,
        'recent_tours': recent_tours,
    }

    return render(request, 'accounts/dashboard.html', context)


@login_required
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, 'accounts/users.html', {'users': users})


@login_required
def tour_list(request):
    tours = Tour.objects.all()
    return render(request, 'accounts/tours.html', {'tours': tours})


@login_required
def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, 'accounts/bookings.html', {'bookings': bookings})


@login_required
def payment_list(request):
    payments = Payment.objects.all()
    return render(request, 'accounts/payments.html', {'payments': payments})


@login_required
def review_list(request):
    reviews = Review.objects.all()
    return render(request, 'accounts/reviews.html', {'reviews': reviews})


@login_required
def report_view(request):
    return render(request, 'accounts/reports.html')


@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')