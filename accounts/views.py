from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse

from .forms import CustomUserCreationForm, CustomLoginForm

User = get_user_model()  # Correctly get the custom user model

def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')

        # Basic validation
        if password1 != password2:
            messages.error(request, "Passwords don't match!")
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'accounts/register.html')

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            # Assuming your CustomUser model has a 'role' field directly:
            user.role = role
            user.save()

            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard or wherever you want

        except Exception as e:
            messages.error(request, f"Error during registration: {str(e)}")

    return render(request, 'accounts/register.html')


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'dashboard')  # Default redirect to dashboard

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")
            return render(request, 'accounts/login.html')

    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def password_reset_request(request):
    """Password reset request view"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
                otp = user.generate_otp()
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP for password reset is: {otp}. It is valid for 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,``````
                )
                messages.success(request, "OTP has been sent to your email.")
                return redirect('password_reset_verify', email=email)
            except User.DoesNotExist:
                messages.error(request, "No user found with this email address.")
    else:
        form = PasswordResetRequestForm()
    return render(request, 'auth/password_reset_request.html', {'form': form})

def password_reset_verify(request, email):
    """Verify OTP and allow password reset"""
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(email=email)
            if user.otp == otp and user.otp_expiry > timezone.now():
                return redirect('password_reset_confirm', email=email, otp=otp)
            else:
                messages.error(request, "Invalid or expired OTP.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, 'auth/password_reset_verify.html', {'email': email})

def password_reset_confirm(request, email, otp):
    """Set new password after OTP verification"""
    try:
        user = User.objects.get(email=email)
        if user.otp != otp or user.otp_expiry < timezone.now():
            messages.error(request, "Invalid or expired OTP.")
            return redirect('password_reset_request')
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                password = form.cleaned_data.get('password')
                user.set_password(password)
                user.otp = None
                user.otp_expiry = None
                user.save()
                messages.success(request, "Password has been reset successfully. You can now login.")
                return redirect('login')
        else:
            form = PasswordResetForm()
        return render(request, 'auth/password_reset_confirm.html', {'form': form})
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('password_reset_request')

# --- Profile Views ---

@login_required
def profile_setup(request):
    """Setup user profile"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('user_dashboard')
    else:
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name
        })
    return render(request, 'profile/setup.html', {'form': form})

@login_required
def user_dashboard(request):
    """User dashboard view"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    upcoming_tours = Booking.objects.filter(
        user=request.user,
        status='confirmed',
        tour_date__gte=datetime.now().date()
    ).order_by('tour_date')
    context = {
        'bookings': bookings,
        'upcoming_tours': upcoming_tours
    }
    return render(request, 'profile/dashboard.html', context)

# Dashboard Views
@login_required
def dashboard(request):
    """Render the dashboard page."""
    # Example static data, replace with actual database queries as needed
    context = {
        'total_users': User.objects.count(),
        'tourist_count': User.objects.filter(role='customer').count(),
        'guide_count': User.objects.filter(role='guide').count(),
        'admin_count': User.objects.filter(role='admin').count(),

        'active_tours': 148,  # Replace with real query
        'total_bookings': 5723,  # Replace with real query
        'total_revenue': '$127,890',  # Replace with real aggregation
        'recent_bookings': [
            {'user': {'username': 'user1'}, 'tour': {'name': 'Paris Explorer'}, 'date': '2025-05-12', 'amount': '299', 'status': 'confirmed'},
            {'user': {'username': 'user2'}, 'tour': {'name': 'Tokyo Adventure'}, 'date': '2025-05-14', 'amount': '450', 'status': 'pending'},
            {'user': {'username': 'user3'}, 'tour': {'name': 'New York City Tour'}, 'date': '2025-05-15', 'amount': '199', 'status': 'cancelled'},
        ],
        # Add other context data as needed
    }
    return render(request, 'accounts/dashboard.html', context)
