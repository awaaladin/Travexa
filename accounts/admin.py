from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import (
    CustomUser, BookingReport, RevenueReport,
    UserGrowthReport, TourPerformanceReport, Tour,
    Review, Booking, Payment, UserProfile, Notification,
    TourImage
)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'is_staff']


admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(BookingReport)
class BookingReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'report_type', 'start_date', 'end_date', 'total_bookings')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'created_by', 'report_type', 'start_date', 'end_date')
        }),
        ('Booking Metrics', {
            'fields': ('total_bookings', 'completed_bookings', 'cancelled_bookings', 'pending_bookings', 'average_booking_value')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RevenueReport)
class RevenueReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'report_type', 'start_date', 'end_date', 'total_revenue', 'net_revenue')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'created_by', 'report_type', 'start_date', 'end_date')
        }),
        ('Revenue Metrics', {
            'fields': ('total_revenue', 'refunded_amount', 'net_revenue')
        }),
        ('Top Performers', {
            'fields': ('most_profitable_tour', 'most_profitable_tour_revenue')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserGrowthReport)
class UserGrowthReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'report_type', 'start_date', 'end_date', 'new_users', 'user_growth_percentage')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'created_by', 'report_type', 'start_date', 'end_date')
        }),
        ('User Metrics', {
            'fields': ('new_users', 'active_users', 'inactive_users', 'user_growth_percentage', 'new_tour_operators')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TourPerformanceReport)
class TourPerformanceReportAdmin(admin.ModelAdmin):
    list_display = ('tour', 'bookings_count', 'revenue', 'average_rating', 'report_period')
    list_filter = ('report_period', 'created_at')
    search_fields = ('tour__title',)
    readonly_fields = ('created_at',)


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'price', 'category', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'location')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'user', 'tour', 'status', 'tour_date', 'total_price')
    list_filter = ('status', 'booking_date')
    search_fields = ('booking_id', 'user__username', 'tour__title')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('payment_method', 'status', 'payment_date')
    search_fields = ('booking__booking_id', 'transaction_id')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('tour', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('tour__title', 'customer__username', 'comment')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'last_activity')
    search_fields = ('user__username', 'phone', 'address')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')


@admin.register(TourImage)
class TourImageAdmin(admin.ModelAdmin):
    list_display = ('tour', 'caption')
    search_fields = ('tour__title', 'caption')
