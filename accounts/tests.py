from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Tour, Booking, Payment, Review, UserProfile

class TravexaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = get_user_model().objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        
        # Create a tour
        self.tour = Tour.objects.create(
            title='Test Tour',
            description='Test Description',
            price=Decimal('100.00'),
            duration=3,
            location='Test Location',
            is_active=True,
            start_date=timezone.now() + timedelta(days=30),
            end_date=timezone.now() + timedelta(days=33)
        )
        
        # Create some bookings
        self.booking = Booking.objects.create(
            customer=self.user,
            tour=self.tour,
            booking_date=timezone.now(),
            total_price=Decimal('100.00'),
            status='confirmed'
        )
        
        # Create a payment
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=Decimal('100.00'),
            method='card',
            status='completed',
            transaction_id='test_txn_123'
        )

    def test_home_view(self):
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/landing_page.html')

    def test_login_required_dashboard(self):
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirects to login
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')

    def test_dashboard_context(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:dashboard'))
        
        # Test dashboard context data
        self.assertTrue('total_bookings' in response.context)
        self.assertTrue('total_spent' in response.context)
        self.assertTrue('upcoming_tours_count' in response.context)
        self.assertTrue('loyalty_points' in response.context)
        self.assertTrue('recent_bookings' in response.context)
        self.assertTrue('popular_tours' in response.context)
        
        # Test actual values
        self.assertEqual(response.context['total_bookings'], 1)
        self.assertEqual(response.context['total_spent'], Decimal('100.00'))
        self.assertEqual(response.context['upcoming_tours_count'], 1)
        self.assertEqual(response.context['loyalty_points'], 100)

    def test_booking_process(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test booking creation
        response = self.client.post(reverse('accounts:booking_create', args=[self.tour.id]), {
            'booking_date': timezone.now().date(),
            'number_of_people': 2
        })
        self.assertEqual(Booking.objects.count(), 2)  # One from setup + one new
        
        # Test booking cancellation
        booking = Booking.objects.latest('created_at')
        response = self.client.post(reverse('accounts:booking_cancel', args=[booking.id]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')

    def test_admin_dashboard(self):
        # Regular user should not access admin dashboard
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Admin should access admin dashboard
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('total_users' in response.context)
        self.assertTrue('total_revenue' in response.context)
        self.assertTrue('active_tours' in response.context)
        self.assertTrue('recent_activities' in response.context)

    def test_user_profile(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test profile view
        response = self.client.get(reverse('accounts:user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/user.html')
        
        # Test profile update
        response = self.client.post(reverse('accounts:user'), {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'updated@example.com',
            'phone': '+1234567890'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        user = get_user_model().objects.get(username='testuser')
        self.assertEqual(user.email, 'updated@example.com')

    def test_tour_visibility(self):
        # Create an inactive tour
        inactive_tour = Tour.objects.create(
            title='Inactive Tour',
            description='Inactive Description',
            price=Decimal('50.00'),
            duration=2,
            location='Test Location',
            is_active=False
        )
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:tour_list'))
        
        # Should only see active tours
        self.assertTrue(self.tour in response.context['tours'])
        self.assertFalse(inactive_tour in response.context['tours'])

    def test_review_system(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Create a review
        response = self.client.post(reverse('accounts:review_create', args=[self.tour.id]), {
            'rating': 5,
            'comment': 'Great tour!'
        })
        
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great tour!')
        self.assertEqual(review.tour, self.tour)
        self.assertEqual(review.customer, self.user)

    def test_payment_process(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Create a new booking
        booking = Booking.objects.create(
            customer=self.user,
            tour=self.tour,
            booking_date=timezone.now(),
            total_price=Decimal('150.00'),
            status='pending'
        )
        
        # Test payment creation
        response = self.client.post(reverse('accounts:payment_create', args=[booking.id]), {
            'payment_method': 'card',
            'amount': '150.00'
        })
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'confirmed')
        self.assertEqual(Payment.objects.filter(booking=booking).count(), 1)
        self.assertEqual(Payment.objects.filter(booking=booking).first().status, 'completed')
