from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import (
    CustomUser, UserProfile, Tour, TourImage, Booking, Payment,
    Review, Notification, AdminReport, UserActivityReport, TourPerformanceReport
)
from .forms import (
    CustomUserCreationForm, UserProfileForm, LoginForm, CustomUserChangeForm,
    BookingForm, PaymentForm, PasswordResetRequestForm, PasswordResetForm
)

import json
import uuid
from datetime import datetime

User = get_user_model()  # Get the custom user model

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile if needed
            try:
                UserProfile.objects.create(user=user)
            except:
                pass
            messages.success(request, "Registration successful! Please login.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(f"Login attempt for user: {username}")  # Debug print
        user = authenticate(request, username=username, password=password)
        print(f"Authentication result: {user}")  # Debug print
        if user is not None:
            login(request, user)
            print(f"User logged in: {getattr(user, 'role', None)}")  # Debug print
            messages.success(request, "Login successful!")
            # Redirect based on role
            if hasattr(user, 'role') and user.role == 'admin':
                print("Redirecting to admin dashboard")  # Debug print
                return redirect('accounts:admin_dashboard')
            print("Redirecting to user dashboard")  # Debug print
            return redirect('accounts:dashboard')
        messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login') # Redirect to the login page

@login_required
def dashboard(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    
    # Get total bookings and calculate growth
    total_bookings = Booking.objects.filter(user=request.user).count()
    last_month_bookings = Booking.objects.filter(
        user=request.user,
        booking_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    booking_growth_percentage = ((last_month_bookings / total_bookings) * 100) if total_bookings > 0 else 0
    
    # Calculate total spent and growth
    total_spent = Payment.objects.filter(
        booking__user=request.user, 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    last_month_spent = Payment.objects.filter(
        booking__user=request.user,
        status='completed',
        payment_date__gte=timezone.now() - timezone.timedelta(days=30)
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    spent_growth_percentage = ((last_month_spent / total_spent) * 100) if total_spent > 0 else 0
    
    # Get upcoming tours
    upcoming_tours = Booking.objects.filter(
        user=request.user,
        status='confirmed',
        tour_date__gt=timezone.now().date()
    ).order_by('tour_date')
    upcoming_tours_count = upcoming_tours.count()
    next_upcoming_tour_date = upcoming_tours.first().tour_date if upcoming_tours.exists() else None
    
    # Get loyalty points (example implementation)
    loyalty_points = total_bookings * 100  # Simple calculation: 100 points per booking
    points_to_next_tier = 1000 - (loyalty_points % 1000)  # Next tier every 1000 points
    
    # Get recent bookings
    recent_bookings = Booking.objects.filter(
        user=request.user
    ).order_by('-booking_date')[:5]
    
    # Get popular tours based on bookings
    popular_tours = Tour.objects.filter(
        is_active=True
    ).annotate(
        total_bookings=models.Count('bookings'),
        total_reviews=models.Count('reviews'),
        average_rating=models.Avg('reviews__rating')
    ).order_by('-total_bookings')[:5]
    
    context = {
        'user_profile': user_profile,
        'user': request.user,
        'total_bookings': total_bookings,
        'booking_growth_percentage': round(booking_growth_percentage, 1),
        'total_spent': total_spent,
        'spent_growth_percentage': round(spent_growth_percentage, 1),
        'upcoming_tours_count': upcoming_tours_count,
        'next_upcoming_tour_date': next_upcoming_tour_date,
        'loyalty_points': loyalty_points,
        'points_to_next_tier': points_to_next_tier,
        'recent_bookings': recent_bookings,
        'popular_tours': popular_tours
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def user(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:user')
        else:
            messages.error(request, "Error updating profile. Please check the form.")
    else:
        user_form = CustomUserChangeForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/user.html', context)


@login_required
def profile_setup(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard') # Redirect to dashboard after profile setup
        else:
            messages.error(request, 'Error updating profile. Please correct the errors.')
    else:
        form = UserProfileForm(instance=user_profile)
    return render(request, 'accounts/profile_setup.html', {'form': form})

@login_required
def profile_view(request):
    # Ensure the user has a profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/user_profile.html')

# --- Tour related views ---
@login_required
def tour_list(request):
    tours = Tour.objects.filter(is_active=True).order_by('-created_at')
    context = {
        'tours': tours
    }
    return render(request, 'accounts/tour_list.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'guide' or u.role == 'admin')
def tour_create(request):
    if request.method == 'POST':
        # Assuming tour form is submitted via request.POST
        # You'll need to create a form for Tour model to handle this
        pass
    return render(request, 'tours/tour_create.html')

@login_required
def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    reviews = Review.objects.filter(tour=tour).order_by('-created_at')
    booking_form = BookingForm(initial={'tour': tour}) # Initialize booking form with tour
    context = {
        'tour': tour,
        'reviews': reviews,
        'booking_form': booking_form
    }
    return render(request, 'tours/tour_detail.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'guide' or u.role == 'admin')
def tour_edit(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.method == 'POST':
        # Handle tour edit form submission
        pass
    return render(request, 'tours/tour_edit.html', {'tour': tour})

@login_required
@user_passes_test(lambda u: u.role == 'guide' or u.role == 'admin')
def tour_delete(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.method == 'POST':
        tour.delete()
        messages.success(request, "Tour deleted successfully.")
        return redirect('tour_list')
    return render(request, 'tours/tour_confirm_delete.html', {'tour': tour})

# --- Booking related views ---
@login_required
def booking_create(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour = tour
            booking.total_price = tour.price # Ensure total_price is set
            booking.save()
            messages.success(request, "Booking created successfully!")
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = BookingForm()
    return render(request, 'bookings/booking_create.html', {'form': form, 'tour': tour})

@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    context = {
        'bookings': bookings
    }
    return render(request, 'accounts/booking_list.html', context)

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    context = {
        'booking': booking
    }
    return render(request, 'bookings/booking_detail.html', context)

@login_required
def booking_cancel(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.info(request, "Booking has been cancelled.")
        return redirect('booking_list')
    return render(request, 'bookings/booking_cancel_confirm.html', {'booking': booking})

# --- Payment related views ---
@login_required
def payment_create(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment_method = form.cleaned_data['payment_method']
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                payment_method=payment_method,
                status='completed',
                transaction_id=f"manual_{uuid.uuid4().hex[:10]}"
            )
            booking.status = 'confirmed'
            booking.save()
            messages.success(request, "Payment successful! Your booking is confirmed.")
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = PaymentForm(initial={'amount': booking.total_price})
    return render(request, 'accounts/payment_form.html', {'form': form, 'booking': booking})


@csrf_exempt
def process_payment(request, booking_id):
    """Simple payment processing endpoint"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
    
    try:
        booking = Booking.objects.get(id=booking_id)
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_price,
            payment_method=request.POST.get('payment_method', 'card'),
            status='completed',
            transaction_id=f'manual_{uuid.uuid4().hex[:10]}'
        )
        booking.status = 'confirmed'
        booking.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# --- Review related views ---
@login_required
def review_create(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating:
            try:
                Review.objects.create(tour=tour, customer=request.user, rating=int(rating), comment=comment)
                messages.success(request, "Your review has been submitted!")
            except Exception as e:
                messages.error(request, f"Could not submit review: {e}")
            return redirect('tour_detail', tour_id=tour.id)
    return redirect('tour_detail', tour_id=tour.id) # Redirect if not POST

# --- Notification related views ---
@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    context = {
        'notifications': notifications
    }
    return render(request, 'accounts/notification_list.html', context)

@login_required
def notification_mark_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

# --- Admin Report Views ---
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_report_list(request):
    reports = AdminReport.objects.all().order_by('-generated_date')
    context = {
        'reports': reports
    }
    return render(request, 'admin/admin_report_list.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_report_create(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        report = None
        if report_type == 'user_activity':
            # Example: Generate a simple user activity report
            total_users = CustomUser.objects.count()
            active_users = CustomUser.objects.filter(last_login__gte=timezone.now() - timezone.timedelta(days=30)).count()
            inactive_users = total_users - active_users
            report = UserActivityReport.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users
            )
        elif report_type == 'tour_performance':
            # Example: Generate a simple tour performance report
            total_tours = Tour.objects.count()
            new_tours_period = Tour.objects.filter(created_at__range=[start_date, end_date]).count()
            most_booked_tour_obj = Tour.objects.annotate(num_bookings=models.Count('bookings')).order_by('-num_bookings').first()
            report = TourPerformanceReport.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                total_tours=total_tours,
                new_tours=new_tours_period,
                most_booked_tour=most_booked_tour_obj.title if most_booked_tour_obj else None,
                most_booked_tour_count=most_booked_tour_obj.num_bookings if most_booked_tour_obj else 0
            )

        if report:
            messages.success(request, f"{report_type.replace('_', ' ').title()} Report generated successfully!")
            return redirect('admin_report_detail', pk=report.pk)
        else:
            messages.error(request, "Failed to generate report.")

    return render(request, 'admin/admin_report_create.html')


@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_report_detail(request, pk):
    report = get_object_or_404(AdminReport, pk=pk)
    # You might want to fetch specific report details based on report.report_type
    if report.report_type == 'user_activity':
        specific_report = get_object_or_404(UserActivityReport, pk=pk) # Assuming AdminReport and UserActivityReport share PKs or are linked
    elif report.report_type == 'tour_performance':
        specific_report = get_object_or_404(TourPerformanceReport, pk=pk)
    else:
        specific_report = None
    context = {
        'report': report,
        'specific_report': specific_report,
    }
    return render(request, 'admin/admin_report_detail.html', context)

# Admin Dashboard Views
@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_dashboard(request):
    # Get dashboard statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(last_login__gte=timezone.now() - timezone.timedelta(days=30)).count()
    user_growth = ((active_users / total_users) * 100) if total_users > 0 else 0
    
    # Revenue statistics
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=models.Sum('amount'))['total'] or 0
    last_month_revenue = Payment.objects.filter(
        status='completed',
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    revenue_growth = ((last_month_revenue / total_revenue) * 100) if total_revenue > 0 else 0
    
    # Tour statistics
    active_tours = Tour.objects.filter(is_active=True).count()
    new_tours = Tour.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Booking statistics
    pending_bookings = Booking.objects.filter(status='pending').count()
    
    # Recent activities
    recent_activities = []
    
    # Get recent bookings
    recent_bookings = Booking.objects.all().order_by('-booking_date')[:5]
    for booking in recent_bookings:
        recent_activities.append({
            'timestamp': booking.created_at,
            'title': f'New Booking: {booking.tour.title}',
            'description': f'by {booking.customer.username}'
        })
    
    # Get recent users
    recent_users = CustomUser.objects.all().order_by('-date_joined')[:5]
    for user in recent_users:
        recent_activities.append({
            'timestamp': user.date_joined,
            'title': f'New User Registration',
            'description': f'{user.username} joined the platform'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]
    
    context = {
        'total_users': total_users,
        'user_growth': round(user_growth, 1),
        'total_revenue': total_revenue,
        'revenue_growth': round(revenue_growth, 1),
        'active_tours': active_tours,
        'tour_growth': new_tours,
        'pending_bookings': pending_bookings,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'accounts/admin/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_activity_log(request):
    activities = []
    
    # Get all relevant activities (bookings, user registrations, reviews, etc.)
    bookings = Booking.objects.all().order_by('-booking_date')
    for booking in bookings:
        activities.append({
            'timestamp': booking.created_at,
            'type': 'booking',
            'title': f'New Booking: {booking.tour.title}',
            'description': f'by {booking.customer.username}',
            'status': booking.status
        })
    
    users = CustomUser.objects.all().order_by('-date_joined')
    for user in users:
        activities.append({
            'timestamp': user.date_joined,
            'type': 'user',
            'title': 'New User Registration',
            'description': f'{user.username} joined the platform',
            'status': 'active' if user.is_active else 'inactive'
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'activities': activities
    }
    
    return render(request, 'accounts/admin/activity_log.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def admin_settings(request):
    if request.method == 'POST':
        # Handle system settings update
        settings_updated = False
        messages.success(request, "Settings updated successfully!")
        return redirect('accounts:admin_settings')
    
    context = {
        'settings': {
            'booking_confirmation_required': True,
            'allow_user_reviews': True,
            'notification_email': 'admin@travexa.com',
            'currency': 'USD',
            'booking_expiry_hours': 24,
        }
    }
    return render(request, 'accounts/admin/settings.html', context)

def home(request):
    """Home page with featured tours"""
    # If user is authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    # Get featured tours for the landing page
    featured_tours = Tour.objects.filter(is_active=True).order_by('-created_at')[:6]
    context = {
        'featured_tours': featured_tours
    }
    return render(request, 'accounts/landing_page.html', context)

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate and send password reset email
                messages.success(request, "If an account exists with that email, you will receive password reset instructions.")
                return redirect('accounts:login')
            except User.DoesNotExist:
                # For security, don't reveal whether the email exists
                messages.success(request, "If an account exists with that email, you will receive password reset instructions.")
                return redirect('accounts:login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

def admin_user_list(request):
    # Placeholder view for admin user list
    return render(request, 'accounts/admin_user_list.html', {})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} has been created successfully.')
            return redirect('admin_user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/admin/user_create.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user_profile = get_object_or_404(UserProfile, user=user)
    context = {
        'user': user,
        'user_profile': user_profile,
        'bookings': Booking.objects.filter(user=user).order_by('-booking_date'),
        'payments': Payment.objects.filter(booking__user=user).order_by('-created_at')
    }
    return render(request, 'accounts/admin/user_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_tour_list(request):
    tours = Tour.objects.all().order_by('-created_at')
    context = {
        'tours': tours,
        'total_tours': tours.count(),
        'active_tours': tours.filter(is_active=True).count(),
        'inactive_tours': tours.filter(is_active=False).count()
    }
    return render(request, 'accounts/admin/tour_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    bookings = Booking.objects.filter(tour=tour).order_by('-booking_date')
    reviews = Review.objects.filter(tour=tour).order_by('-created_at')
    
    context = {
        'tour': tour,
        'bookings': bookings,
        'reviews': reviews,
        'booking_count': bookings.count(),
        'revenue': bookings.filter(status='confirmed').aggregate(total=models.Sum('total_price'))['total'] or 0,
        'average_rating': reviews.aggregate(avg=models.Avg('rating'))['avg'] or 0
    }
    return render(request, 'accounts/admin/tour_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_tour_create(request):
    if request.method == 'POST':
        # Handle form submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        duration = request.POST.get('duration')
        location = request.POST.get('location')
        
        tour = Tour.objects.create(
            title=title,
            description=description,
            price=price,
            duration=duration,
            location=location,
            is_active=True
        )
        
        messages.success(request, f'Tour "{tour.title}" has been created successfully.')
        return redirect('admin_tour_detail', tour_id=tour.id)
        
    return render(request, 'accounts/admin/tour_create.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_tour_edit(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    
    if request.method == 'POST':
        # Handle form submission
        tour.title = request.POST.get('title')
        tour.description = request.POST.get('description')
        tour.price = request.POST.get('price')
        tour.duration = request.POST.get('duration')
        tour.location = request.POST.get('location')
        tour.is_active = request.POST.get('is_active') == 'on'
        tour.save()
        
        messages.success(request, f'Tour "{tour.title}" has been updated successfully.')
        return redirect('admin_tour_detail', tour_id=tour.id)
    
    context = {'tour': tour}
    return render(request, 'accounts/admin/tour_edit.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_tour_delete(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    
    if request.method == 'POST':
        tour_title = tour.title
        tour.delete()
        messages.success(request, f'Tour "{tour_title}" has been deleted successfully.')
        return redirect('admin_tour_list')
    
    context = {'tour': tour}
    return render(request, 'accounts/admin/tour_delete.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def api_booking_stats(request):
    # Get booking statistics for the last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    bookings = Booking.objects.filter(created_at__gte=thirty_days_ago)
    
    # Group bookings by date
    bookings_by_date = bookings.annotate(
        date=models.functions.TruncDate('created_at')
    ).values('date').annotate(
        count=models.Count('id')
    ).order_by('date')
    
    data = {
        'labels': [],
        'data': []
    }
    
    for booking in bookings_by_date:
        data['labels'].append(booking['date'].strftime('%Y-%m-%d'))
        data['data'].append(booking['count'])
    
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
def api_revenue_stats(request):
    # Get revenue statistics for the last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    payments = Payment.objects.filter(
        created_at__gte=thirty_days_ago,
        status='completed'
    )
    
    # Group payments by date
    revenue_by_date = payments.annotate(
        date=models.functions.TruncDate('created_at')
    ).values('date').annotate(
        revenue=models.Sum('amount')
    ).order_by('date')
    
    data = {
        'labels': [],
        'data': []
    }
    
    for revenue in revenue_by_date:
        data['labels'].append(revenue['date'].strftime('%Y-%m-%d'))
        data['data'].append(float(revenue['revenue']))
    
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
def api_user_stats(request):
    # Get user registration statistics for the last 30 days
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    users = CustomUser.objects.filter(date_joined__gte=thirty_days_ago)
    
    # Group users by registration date
    users_by_date = users.annotate(
        date=models.functions.TruncDate('date_joined')
    ).values('date').annotate(
        count=models.Count('id')
    ).order_by('date')
    
    data = {
        'labels': [],
        'data': []
    }
    
    for user_count in users_by_date:
        data['labels'].append(user_count['date'].strftime('%Y-%m-%d'))
        data['data'].append(user_count['count'])
    
    return JsonResponse(data)

@login_required
def edit_profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = CustomUserChangeForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    return render(request, 'accounts/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

def landing_page(request):
    form = CustomUserCreationForm()
    return render(request, 'accounts/landing_page.html', {'form': form})

def respond_to_reviews(request):
    return render(request, 'accounts/respond_to_reviews.html')

def user_reviews(request):
    return render(request, 'accounts/user_reviews.html')

def travel_history(request):
    """Simple placeholder view for Travel History page."""
    return render(request, 'accounts/travel_history.html')

def tour_area_map(request):
    """Simple placeholder view for Tour Area Map page."""
    return render(request, 'accounts/tour_area_map.html')

def support(request):
    """Simple placeholder view for Support page."""
    return render(request, 'accounts/support.html')