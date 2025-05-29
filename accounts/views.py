from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser, UserProfile, Tour, TourImage, Booking, Payment
from .forms import (
    UserRegistrationForm, UserProfileForm, LoginForm,
    BookingForm, PaymentForm, PasswordResetRequestForm, PasswordResetForm
)

import json
from datetime import datetime

User = get_user_model()  # Correctly get the custom user model

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Registration successful! Welcome to our tour booking platform.")
            return redirect('profile_setup')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Login successful!")
                next_page = request.GET.get('next', 'home')
                return redirect(next_page)
            else:
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard Views
@login_required
def dashboard(request):
    """Admin dashboard page (example)"""
    context = {
        'total_users': User.objects.count(),
        'tourist_count': User.objects.filter(role='customer').count(),
        'guide_count': User.objects.filter(role='guide').count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'active_tours': Tour.objects.filter(is_active=True).count(),
        'total_bookings': Booking.objects.count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(models.Sum('amount'))['amount__sum'] or 0,
        'recent_bookings': Booking.objects.order_by('-booking_date')[:5],
    }
    return render(request, 'accounts/dashboard.html', context)

# --- Tour Views ---

def home(request):
    """Home page with featured tours"""
    featured_tours = Tour.objects.filter(is_active=True).order_by('-created_at')[:6]
    context = {
        'featured_tours': featured_tours
    }
    return render(request, 'tours/home.html', context)

def tour_list(request):
    """List all tours with search and filter"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    country = request.GET.get('country', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    tours = Tour.objects.filter(is_active=True)
    if query:
        tours = tours.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(country__icontains=query)
        )
    if category:
        tours = tours.filter(category=category)
    if country:
        tours = tours.filter(country=country)
    if min_price:
        tours = tours.filter(price__gte=min_price)
    if max_price:
        tours = tours.filter(price__lte=max_price)
    countries = Tour.objects.filter(is_active=True).values_list('country', flat=True).distinct()
    context = {
        'tours': tours,
        'query': query,
        'category': category,
        'country': country,
        'min_price': min_price,
        'max_price': max_price,
        'countries': countries,
        'categories': dict(Tour.CATEGORY_CHOICES)
    }
    return render(request, 'tours/tour_list.html', context)

def tour_detail(request, tour_id):
    """Display detailed information about a tour"""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    available_dates = tour.get_available_dates()
    context = {
        'tour': tour,
        'available_dates': available_dates,
        'tour_images': tour.images.all()
    }
    return render(request, 'tours/tour_detail.html', context)

def tour_map(request, tour_id):
    """Display a map of the tour location"""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    if not tour.latitude or not tour.longitude:
        messages.error(request, "Map coordinates not available for this tour.")
        return redirect('tour_detail', tour_id=tour.id)
    context = {
        'tour': tour,
        'api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'tours/tour_map.html', context)

# --- Booking Views ---

@login_required
def booking_create(request, tour_id):
    """Create a new booking for a tour"""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    if request.method == 'POST':
        form = BookingForm(request.POST, tour=tour)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.tour = tour
            booking.total_price = tour.price * booking.participants
            booking.save()
            messages.success(request, "Booking created successfully! Proceed to payment.")
            return redirect('payment_create', booking_id=booking.booking_id)
    else:
        form = BookingForm(tour=tour)
    context = {
        'form': form,
        'tour': tour
    }
    return render(request, 'bookings/booking_form.html', context)

@login_required
def booking_list(request):
    """List all bookings for the current user"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    context = {
        'bookings': bookings
    }
    return render(request, 'bookings/booking_list.html', context)

@login_required
def booking_detail(request, booking_id):
    """Display detailed information about a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    payments = Payment.objects.filter(booking=booking)
    context = {
        'booking': booking,
        'payments': payments
    }
    return render(request, 'bookings/booking_detail.html', context)

@login_required
def booking_cancel(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    if request.method == 'POST':
        if booking.cancel():
            messages.success(request, "Booking cancelled successfully!")
        else:
            messages.error(request, "Unable to cancel booking. It may already be completed or cancelled.")
        return redirect('booking_detail', booking_id=booking.booking_id)
    context = {
        'booking': booking
    }
    return render(request, 'bookings/booking_cancel.html', context)

# --- Payment Views ---

@login_required
def payment_create(request, booking_id):
    """Create a new payment for a booking"""
    import stripe
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    existing_payments = Payment.objects.filter(booking=booking, status='completed')
    if existing_payments.exists():
        messages.info(request, "This booking is already paid.")
        return redirect('booking_detail', booking_id=booking.booking_id)
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.booking = booking
            payment.payment_method = 'stripe'
            payment.save()
            payment_method_id = request.POST.get('payment_method_id')
            if not payment_method_id:
                messages.error(request, "Payment method information is missing.")
                return render(request, 'payments/payment_form.html', {
                    'form': form,
                    'booking': booking,
                    'stripe_public_key': stripe_public_key
                })
            payment_details = {
                'payment_method_id': payment_method_id
            }
            if payment.process_payment(payment_details):
                messages.success(request, "Payment processed successfully!")
                send_payment_confirmation_email(payment)
                return redirect('booking_detail', booking_id=booking.booking_id)
            else:
                messages.error(request, "Payment processing failed. Please check your card details and try again.")
    else:
        form = PaymentForm(initial={'amount': booking.total_price})
    amount_in_cents = int(booking.total_price * 100)
    context = {
        'form': form,
        'booking': booking,
        'amount_in_cents': amount_in_cents,
        'stripe_public_key': stripe_public_key,
        'client_secret': _create_payment_intent(booking)
    }
    return render(request, 'payments/payment_form.html', context)

def _create_payment_intent(booking):
    """Create a payment intent with Stripe and return the client secret"""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(booking.total_price * 100),
            currency='usd',
            metadata={
                'booking_id': str(booking.booking_id),
                'user_email': booking.user.email,
                'tour_name': booking.tour.title
            }
        )
        return intent.client_secret
    except Exception:
        return None

def send_payment_confirmation_email(payment):
    """Send payment confirmation email to user"""
    subject = f"Payment Confirmation - Booking #{payment.booking.booking_id}"
    message = f"""
    Dear {payment.booking.user.get_full_name()},

    Thank you for your payment of ${payment.amount} for your booking of {payment.booking.tour.title}.

    Booking Details:
    - Booking ID: {payment.booking.booking_id}
    - Tour: {payment.booking.tour.title}
    - Date: {payment.booking.tour_date}
    - Participants: {payment.booking.participants}
    - Payment Amount: ${payment.amount}
    - Payment Status: {payment.get_status_display()}
    - Transaction ID: {payment.transaction_id}

    Your booking is now confirmed. You'll receive your e-ticket shortly.

    If you have any questions, please contact our customer support.

    Thank you for choosing our service!
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [payment.booking.user.email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

# --- API Endpoints ---

def get_available_dates(request, tour_id):
    """API endpoint to get available dates for a tour"""
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    available_dates = tour.get_available_dates()
    date_strings = [date.strftime('%Y-%m-%d') for date in available_dates]
    return JsonResponse({'available_dates': date_strings})

@csrf_exempt
def stripe_webhook(request):
    """Webhook for Stripe payment notifications"""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if request.method == 'POST':
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            data_object = event.data.object
            if event.type == 'payment_intent.succeeded':
                transaction_id = data_object.id
                try:
                    payment = Payment.objects.get(transaction_id=transaction_id)
                    payment.status = 'completed'
                    payment.save()
                    payment.booking.status = 'confirmed'
                    payment.booking.save()
                except Payment.DoesNotExist:
                    pass
            elif event.type == 'charge.refunded':
                payment_intent_id = data_object.payment_intent
                try:
                    payment = Payment.objects.get(transaction_id=payment_intent_id)
                    payment.status = 'refunded'
                    payment.save()
                except Payment.DoesNotExist:
                    pass
            elif event.type == 'payment_intent.payment_failed':
                transaction_id = data_object.id
                try:
                    payment = Payment.objects.get(transaction_id=transaction_id)
                    payment.status = 'failed'
                    payment.save()
                except Payment.DoesNotExist:
                    pass
            return JsonResponse({'status': 'success'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid payload'}, status=400)
        except stripe.error.SignatureVerificationError:
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def user(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('accounts:user')
    return render(request, 'accounts/user.html')