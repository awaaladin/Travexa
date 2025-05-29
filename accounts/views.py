from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required

User = get_user_model()


def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')

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
            user.role = role
            user.save()
            login(request, user)
            return redirect('accounts:dashboard')
        except Exception as e:
            messages.error(request, f"Error during registration: {str(e)}")

    return render(request, 'accounts/register.html')


def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'accounts/login.html')


def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Render the dashboard page."""
    context = {
        'total_users': User.objects.count(),
        'tourist_count': User.objects.filter(role='customer').count(),
        'guide_count': User.objects.filter(role='guide').count(),
        'admin_count': User.objects.filter(role='admin').count(),

        'active_tours': 148,
        'total_bookings': 5723,
        'total_revenue': '$127,890',
        'recent_bookings': [
            {'user': {'username': 'user1'}, 'tour': {'name': 'Paris Explorer'}, 'date': '2025-05-12', 'amount': '299', 'status': 'confirmed'},
            {'user': {'username': 'user2'}, 'tour': {'name': 'Tokyo Adventure'}, 'date': '2025-05-14', 'amount': '450', 'status': 'pending'},
            {'user': {'username': 'user3'}, 'tour': {'name': 'New York City Tour'}, 'date': '2025-05-15', 'amount': '199', 'status': 'cancelled'},
        ],
    }
    return render(request, 'accounts/dashboard.html', context)


def user(request):
    """Render the user profile page."""
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:user')

    return render(request, 'accounts/user.html')