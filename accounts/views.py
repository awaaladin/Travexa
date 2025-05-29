from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .forms import (
    CustomUserCreationForm,
    CustomLoginForm,
    ReviewForm,
    ReviewResponseForm,
    ReportGenerationForm,
    BookingForm,
    DateRangeForm,
)
from .models import (
    CustomUser,
    Tour,
    Review,
    ReviewResponse,
    Booking,
    BookingReport,
    RevenueReport,
    UserGrowthReport,
    TourPerformanceReport,
)

User = get_user_model()


# Utility Functions
def is_admin(user):
    """Check if the user is an admin."""
    return user.is_superuser or user.is_staff


# Authentication Views
def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.POST.get('next', 'dashboard'))
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('login')


# Dashboard Views
@login_required
def dashboard(request):
    """Render the dashboard page."""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    context = {
        'total_users': User.objects.count(),
        'tourist_count': User.objects.filter(role='customer').count(),
        'guide_count': User.objects.filter(role='guide').count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'recent_bookings': Booking.objects.all().order_by('-created_at')[:5],
        'total_revenue': Booking.objects.filter(status='completed').aggregate(Sum('total_price'))['total_price__sum'] or 0,
        'bookings_count': Booking.objects.filter(created_at__date__range=(start_date, end_date)).count(),
        'new_users': User.objects.filter(date_joined__date__range=(start_date, end_date)).count(),
        'avg_rating': Review.objects.filter(
            created_at__date__range=(start_date, end_date)
        ).aggregate(avg=Avg('rating', default=0))['avg'],
    }
    return render(request, 'accounts/dashboard.html', context)


# Tour Booking Views
@login_required
def book_tour(request, tour_id):
    """Handle tour booking."""
    tour = get_object_or_404(Tour, id=tour_id)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour = tour
            booking.total_price = tour.price * form.cleaned_data['number_of_people']
            booking.save()
            messages.success(request, "Tour booked successfully!")
            return redirect('dashboard')
    else:
        form = BookingForm(initial={'tour': tour})

    return render(request, 'accounts/book_tour.html', {'form': form, 'tour': tour})


# Review Management Views
@login_required
def add_review(request, tour_id):
    """Add a review for a tour."""
    tour = get_object_or_404(Tour, id=tour_id)

    if Review.objects.filter(tour=tour, user=request.user).exists():
        messages.error(request, "You have already reviewed this tour.")
        return redirect('tour_detail', tour_id=tour_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.tour = tour
            review.save()
            messages.success(request, "Review submitted successfully!")
            return redirect('tour_detail', tour_id=tour_id)
    else:
        form = ReviewForm()

    return render(request, 'accounts/add_review.html', {'form': form, 'tour': tour})


@login_required
def edit_review(request, review_id):
    """Edit an existing review."""
    review = get_object_or_404(Review, id=review_id)

    if review.user != request.user:
        return HttpResponseForbidden("You cannot edit someone else's review.")

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully!")
            return redirect('tour_detail', tour_id=review.tour.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'accounts/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    """Delete a review."""
    review = get_object_or_404(Review, id=review_id)

    if review.user != request.user:
        return HttpResponseForbidden("You cannot delete someone else's review.")

    if request.method == 'POST':
        review.delete()
        messages.success(request, "Review deleted successfully!")
        return redirect('dashboard')

    return render(request, 'accounts/delete_review_confirm.html', {'review': review})


@login_required
def respond_to_review(request, review_id):
    """Respond to a review."""
    review = get_object_or_404(Review, id=review_id)

    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff can respond to reviews.")

    try:
        response = review.response
    except ReviewResponse.DoesNotExist:
        response = None

    if request.method == 'POST':
        form = ReviewResponseForm(request.POST, instance=response)
        if form.is_valid():
            response = form.save(commit=False)
            response.review = review
            response.responder = request.user
            response.save()
            messages.success(request, "Response submitted successfully!")
            return redirect('dashboard')
    else:
        form = ReviewResponseForm(instance=response)

    return render(request, 'accounts/respond_to_review.html', {'form': form, 'review': review})


# Reporting Views
@login_required
@user_passes_test(is_admin)
def generate_report(request):
    """Generate reports."""
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            # Logic for generating reports
            messages.success(request, "Report generated successfully!")
            return redirect('dashboard')
    else:
        form = ReportGenerationForm()

    return render(request, 'accounts/generate_report.html', {'form': form})

# Reporting Detail Views

@login_required
@user_passes_test(is_admin)
def view_booking_report(request, report_id):
    """Display a booking report."""
    report = get_object_or_404(BookingReport, id=report_id)
    return render(request, 'accounts/view_booking_report.html', {'report': report})

@login_required
@user_passes_test(is_admin)
def view_revenue_report(request, report_id):
    """Display a revenue report."""
    report = get_object_or_404(RevenueReport, id=report_id)
    return render(request, 'accounts/view_revenue_report.html', {'report': report})

@login_required
@user_passes_test(is_admin)
def view_user_growth_report(request, report_id):
    """Display a user growth report."""
    report = get_object_or_404(UserGrowthReport, id=report_id)
    return render(request, 'accounts/view_user_growth_report.html', {'report': report})

@login_required
@user_passes_test(is_admin)
def view_tour_performance_report(request, report_id):
    """Display a tour performance report."""
    report = get_object_or_404(TourPerformanceReport, id=report_id)
    return render(request, 'accounts/view_tour_performance_report.html', {'report': report})

# API Endpoints for Charts/Stats
from django.views.decorators.http import require_GET

@login_required
@require_GET
def booking_stats_api(request):
    """Return JSON booking stats for chart rendering."""
    data = {
        'labels': ['Jan', 'Feb', 'Mar'],
        'data': [10, 15, 7],
    }
    return JsonResponse(data)

@login_required
@require_GET
def rating_stats_api(request):
    """Return JSON rating stats for chart rendering."""
    data = {
        'labels': ['5 Stars', '4 Stars', '3 Stars'],
        'data': [50, 30, 20],
    }

    return JsonResponse(data)





