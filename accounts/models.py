from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
import uuid

# --- Custom User Model ---
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('guide', 'Guide'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return self.username

# --- User Profile ---
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# --- Tour Model ---
class Tour(models.Model):
    CATEGORY_CHOICES = (
        ('adventure', 'Adventure'),
        ('cultural', 'Cultural'),
        ('nature', 'Nature'),
        ('urban', 'Urban'),
        ('beach', 'Beach'),
        ('historical', 'Historical'),
        ('food', 'Food & Culinary'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    max_participants = models.PositiveIntegerField()
    featured_image = models.ImageField(upload_to='tour_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.title

    def get_available_dates(self):
        from datetime import date, timedelta
        booked_dates = Booking.objects.filter(
            tour=self, 
            status__in=['confirmed', 'pending'],
            tour_date__gte=date.today()
        ).values_list('tour_date', flat=True)
        available_dates = []
        for i in range(90):
            check_date = date.today() + timedelta(days=i)
            if check_date not in booked_dates:
                available_dates.append(check_date)
        return available_dates

# --- Tour Images ---
class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='tour_images/')
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.tour.title}"

# --- Booking Model ---
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    booking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)
    tour_date = models.DateField()
    participants = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)

    def __str__(self):
        return f"Booking {self.booking_id} - {self.user.username} - {self.tour.title}"

    def cancel(self):
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.save()
            payments = Payment.objects.filter(booking=self, status='completed')
            for payment in payments:
                payment.issue_refund()
            return True
        return False

# --- Payment Model ---
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ('stripe', 'Credit/Debit Card'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Booking {self.booking.booking_id} - {self.amount}"

    def process_payment(self, payment_details):
        import stripe
        from django.conf import settings
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(self.amount * 100),
                currency='usd',
                payment_method=payment_details.get('payment_method_id'),
                confirm=True,
                description=f"Payment for booking {self.booking.booking_id}",
                metadata={
                    'booking_id': str(self.booking.booking_id),
                    'user_email': self.booking.user.email,
                    'tour_name': self.booking.tour.title
                }
            )
            self.transaction_id = payment_intent.id
            self.status = 'completed'
            self.save()
            self.booking.status = 'confirmed'
            self.booking.save()
            return True
        except stripe.error.CardError:
            self.status = 'failed'
            self.save()
            return False
        except (stripe.error.RateLimitError, 
                stripe.error.InvalidRequestError, 
                stripe.error.AuthenticationError,
                stripe.error.APIConnectionError,
                stripe.error.StripeError):
            self.status = 'failed'
            self.save()
            return False

    def issue_refund(self):
        if self.status == 'completed' and self.transaction_id:
            import stripe
            from django.conf import settings
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                stripe.Refund.create(
                    payment_intent=self.transaction_id,
                    reason='requested_by_customer'
                )
                self.status = 'refunded'
                self.save()
                return True
            except stripe.error.StripeError:
                return False
        return False