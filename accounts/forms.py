from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.utils import timezone
from django.db.models import Avg, Count, Q, F
from datetime import timedelta
from collections import defaultdict
from .models import CustomUser, Review, ReviewResponse, Tour, Booking


# Booking Form
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['tour', 'booking_date', 'number_of_people', 'notes']
        widgets = {
            'booking_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


# User Forms
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role']


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


# Review Forms
class ReviewForm(forms.ModelForm):
    """Form for users to create or edit reviews"""
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 5,
            'step': 1,
        })
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your experience with this tour...'
        })
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']


class ReviewResponseForm(forms.ModelForm):
    """Form for tour operators to respond to reviews"""
    response_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Respond to this review...'
        })
    )

    class Meta:
        model = ReviewResponse
        fields = ['response_text']


# Reporting Forms
class DateRangeForm(forms.Form):
    """
    Form for selecting a date range for reports
    """
    DATE_RANGE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom Range'),
    ]

    date_range = forms.ChoiceField(
        choices=DATE_RANGE_CHOICES,
        initial='monthly',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'date-range-select'})
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'start-date',
            }
        )
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'end-date',
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if date_range == 'custom':
            if not start_date:
                self.add_error('start_date', 'Please provide a start date for custom range')
            if not end_date:
                self.add_error('end_date', 'Please provide an end date for custom range')

            if start_date and end_date and start_date > end_date:
                self.add_error('end_date', 'End date must be after start date')

            today = timezone.now().date()
            if start_date and start_date > today:
                self.add_error('start_date', 'Start date cannot be in the future')
            if end_date and end_date > today:
                self.add_error('end_date', 'End date cannot be in the future')

        return cleaned_data


class ReportGenerationForm(DateRangeForm):
    """
    Form for selecting report type and date range
    """
    REPORT_TYPE_CHOICES = [
        ('booking', 'Booking Report'),
        ('revenue', 'Revenue Report'),
        ('user_growth', 'User Growth Report'),
        ('tour_performance', 'Tour Performance Report'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# Analytics
class ReviewAnalytics:
    """
    Class to generate analytics and reports about the review system
    """
    @staticmethod
    def get_tour_review_summary(tour_id):
        try:
            tour = Tour.objects.get(id=tour_id)
            total_reviews = tour.reviews.count()
            avg_rating = tour.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            rating_distribution = {i: tour.reviews.filter(rating=i).count() for i in range(1, 6)}
            rating_percentages = {
                rating: (count / total_reviews * 100) if total_reviews > 0 else 0
                for rating, count in rating_distribution.items()
            }
            return {
                'tour_name': tour.title,
                'total_reviews': total_reviews,
                'average_rating': round(avg_rating, 1),
                'rating_distribution': rating_distribution,
                'rating_percentages': rating_percentages,
            }
        except Tour.DoesNotExist:
            return None

    @staticmethod
    def get_user_review_stats(user_id):
        reviews = Review.objects.filter(user_id=user_id)
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        return {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 1),
        }