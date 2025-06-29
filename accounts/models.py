from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# --- Custom User ---
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
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
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
    notes = models.TextField(blank=True, null=True)  # optional notes field

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
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
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
        """Process a payment with the given details."""
        try:
            # TODO: Implement payment processing logic based on payment_method
            self.status = 'completed'
            self.save()
            self.booking.status = 'confirmed'
            self.booking.save()
            return True
        except Exception:
            self.status = 'failed'
            self.save()
            return False

    def issue_refund(self):
        """Issue a refund for the payment."""
        if self.status == 'completed':
            try:
                # TODO: Implement refund logic based on payment_method
                self.status = 'refunded'
                self.save()
                return True
            except Exception:
                return False
        return False

# --- Booking Report ---
class BookingReport(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    report_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    total_bookings = models.PositiveIntegerField(default=0)
    completed_bookings = models.PositiveIntegerField(default=0)
    cancelled_bookings = models.PositiveIntegerField(default=0)
    pending_bookings = models.PositiveIntegerField(default=0)
    average_booking_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# --- Revenue Report ---
class RevenueReport(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    report_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    most_profitable_tour = models.CharField(max_length=255, blank=True, null=True)
    most_profitable_tour_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# --- User Growth Report ---
class UserGrowthReport(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    report_type = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    inactive_users = models.PositiveIntegerField(default=0)
    user_growth_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    new_tour_operators = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# --- Review Model ---
class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )
    
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.customer.username} for {self.tour.title}"

# --- Notification Model ---
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('booking', 'Booking'),
        ('review', 'Review'),
        ('system', 'System'),
        ('payment', 'Payment'),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)  # Optional link to relevant page

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"

# --- Admin Report ---
class AdminReport(models.Model):
    REPORT_TYPES = (
        ('revenue', 'Revenue Report'),
        ('user_activity', 'User Activity Report'),
        ('tour_performance', 'Tour Performance Report'),
        ('custom', 'Custom Report'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # Stores the report data in JSON format
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.title}"

# --- User Activity Report ---
class UserActivityReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_reports')
    login_count = models.IntegerField(default=0)
    bookings_made = models.IntegerField(default=0)
    reviews_written = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    report_period = models.DateField()  # The date this report represents
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_period']
        unique_together = ['user', 'report_period']

    def __str__(self):
        return f"Activity Report for {self.user.username} - {self.report_period}"

# --- Tour Performance Report ---
class TourPerformanceReport(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='performance_reports')
    bookings_count = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    report_period = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_period']
        unique_together = ['tour', 'report_period']

    def __str__(self):
        return f"Performance Report for {self.tour.title} - {self.report_period}"
