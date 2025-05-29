from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# Custom User Model
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('guide', 'Guide'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    ROLE_CHOICES = (
        ('tourist', 'Tourist'),
        ('operator', 'Tour Operator'),
        ('admin', 'Administrator'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tourist')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Tour Model
class Tour(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in days")
    category = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='tour_images/', null=True, blank=True)

    def __str__(self):
        return self.title

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum([review.rating for review in reviews]) / len(reviews)
        return 0


# Booking Model
class Booking(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    booking_date = models.DateField(default=timezone.now)
    number_of_people = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"{self.user.username} - {self.tour.title} ({self.status})"


# Review and Response Models
class Review(models.Model):
    RATING_CHOICES = (
        (1, '1 - Poor'),
        (2, '2 - Below Average'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1-5 stars')
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'tour']
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')

    def __str__(self):
        return f"{self.user.username}'s review for {self.tour.title}"


class ReviewResponse(models.Model):
    review = models.OneToOneField(
        Review,
        on_delete=models.CASCADE,
        related_name='response'
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_responses',
        help_text=_('Tour operator responding to the review')
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Response to {self.review}"


# Reporting Models
class Report(models.Model):
    REPORT_TYPES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)s_reports'
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"


class BookingReport(Report):
    total_bookings = models.IntegerField()
    completed_bookings = models.IntegerField()
    cancelled_bookings = models.IntegerField()
    pending_bookings = models.IntegerField()
    average_booking_value = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _('Booking Report')
        verbose_name_plural = _('Booking Reports')


class RevenueReport(Report):
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    refunded_amount = models.DecimalField(max_digits=12, decimal_places=2)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    most_profitable_tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        related_name='revenue_reports'
    )
    most_profitable_tour_revenue = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = _('Revenue Report')
        verbose_name_plural = _('Revenue Reports')


class UserGrowthReport(Report):
    new_users = models.IntegerField()
    active_users = models.IntegerField()
    inactive_users = models.IntegerField()
    user_growth_percentage = models.DecimalField(max_digits=8, decimal_places=2)
    new_tour_operators = models.IntegerField()

    class Meta:
        verbose_name = _('User Growth Report')
        verbose_name_plural = _('User Growth Reports')


class TourPerformanceReport(Report):
    total_tours = models.IntegerField()
    new_tours = models.IntegerField()
    most_booked_tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performance_reports'
    )
    most_booked_tour_count = models.IntegerField()
    highest_rated_tour = models.ForeignKey(
        Tour,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rating_reports'
    )
    highest_rated_tour_rating = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        verbose_name = _('Tour Performance Report')
        verbose_name_plural = _('Tour Performance Reports')