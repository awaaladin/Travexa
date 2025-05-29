from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings

from .forms import CustomUserCreationForm, CustomLoginForm, BookingForm, PaymentForm
from tours.models import Tour
from bookings.models import Booking, Payment

User = get_user_model()

# --- Authentication Views ---

def register_view(request):
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
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error during registration: {str(e)}")

    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', 'dashboard')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
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

# --- Tour Views ---

def home(request):
    featured_tours = Tour.objects.filter(is_active=True).order_by('-created_at')[:6]
    return render(request, 'tours/home.html', {'featured_tours': featured_tours})

def tour_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    country = request.GET.get('country', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    tours = Tour.objects.filter(is_active=True)
    if query:
        tours = tours.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query) | Q(country__icontains=query))
    if category:
        tours = tours.filter(category=category)
    if country:
        tours = tours.filter(country=country)
    if min_price:
        tours = tours.filter(price__gte=min_price)
    if max_price:
        tours = tours.filter(price__lte=max_price)
    countries = Tour.objects.filter(is_active=True).values_list('country', flat=True).distinct()
    return render(request, 'tours/tour_list.html', {
        'tours': tours,
        'query': query,
        'category': category,
        'country': country,
        'min_price': min_price,
        'max_price': max_price,
        'countries': countries,
        'categories': dict(Tour.CATEGORY_CHOICES)
    })

def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    return render(request, 'tours/tour_detail.html', {
        'tour': tour,
        'available_dates': tour.get_available_dates(),
        'tour_images': tour.images.all()
    })

def tour_map(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    if not tour.latitude or not tour.longitude:
        messages.error(request, "Map coordinates not available for this tour.")
        return redirect('tour_detail', tour_id=tour.id)
    return render(request, 'tours/tour_map.html', {
        'tour': tour,
        'api_key': settings.GOOGLE_MAPS_API_KEY
    })

# --- Booking Views ---

@login_required
def booking_create(request, tour_id):
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
    return render(request, 'bookings/booking_form.html', {'form': form, 'tour': tour})

@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'bookings/booking_list.html', {'bookings': bookings})

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    payments = Payment.objects.filter(booking=booking)
    return render(request, 'bookings/booking_detail.html', {'booking': booking, 'payments': payments})

@login_required
def booking_cancel(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    if request.method == 'POST':
        if booking.cancel():
            messages.success(request, "Booking cancelled successfully!")
        else:
            messages.error(request, "Unable to cancel booking.")
        return redirect('booking_detail', booking_id=booking.booking_id)
    return render(request, 'bookings/booking_cancel.html', {'booking': booking})

# --- Payment Views ---

@login_required
def payment_create(request, booking_id):
    import stripe
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    if Payment.objects.filter(booking=booking, status='completed').exists():
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
                return render(request, 'payments/payment_form.html', {'form': form, 'booking': booking, 'stripe_public_key': stripe_public_key})
            if payment.process_payment({'payment_method_id': payment_method_id}):
                messages.success(request, "Payment processed successfully!")
                send_payment_confirmation_email(payment)
                return redirect('booking_detail', booking_id=booking.booking_id)
            else:
                messages.error(request, "Payment processing failed.")
    else:
        form = PaymentForm(initial={'amount': booking.total_price})
    return render(request, 'payments/payment_form.html', {
        'form': form,
        'booking': booking,
        'amount_in_cents': int(booking.total_price * 100),
        'stripe_public_key': stripe_public_key,
        'client_secret': _create_payment_intent(booking)
    })

def _create_payment_intent(booking):
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

    Thank you for choosing our service!
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [payment.booking.user.email], fail_silently=False)

# --- API Endpoints ---

def get_available_dates(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id, is_active=True)
    return JsonResponse({'available_dates': [date.strftime('%Y-%m-%d') for date in tour.get_available_dates()]})

@csrf_exempt
def stripe_webhook(request):
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
                payment = Payment.objects.filter(transaction_id=transaction_id).first()
                if payment:
                    payment.status = 'completed'
                    payment.save()
                    payment.booking.status = 'confirmed'
                    payment.booking.save()
            elif event.type == 'charge.refunded':
                payment_intent_id = data_object.payment_intent
                payment = Payment.objects.filter(transaction_id=payment_intent_id).first()
                if payment:
                    payment.status = 'refunded'
                    payment.save()
            elif event.type == 'payment_intent.payment_failed':
                transaction_id = data_object.id
                payment = Payment.objects.filter(transaction_id=transaction_id).first()
                if payment:
                    payment.status = 'failed'
                    payment.save()
            return JsonResponse({'status': 'success'})
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