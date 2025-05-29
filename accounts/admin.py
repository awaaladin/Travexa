from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, BookingReport, RevenueReport, UserGrowthReport, TourPerformanceReport


# Custom User Admin
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'is_staff']


admin.site.register(CustomUser, CustomUserAdmin)


# Reporting Admins
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
            'fields': ('total_bookings', 'completed_bookings', 'cancelled_bookings', 
                      'pending_bookings', 'average_booking_value')
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
    list_display = ('title', 'created_by', 'report_type', 'start_date', 'end_date', 'total_tours', 'new_tours')
    list_filter = ('report_type', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Report Information', {
            'fields': ('title', 'description', 'created_by', 'report_type', 'start_date', 'end_date')
        }),
        ('Tour Metrics', {
            'fields': ('total_tours', 'new_tours')
        }),
        ('Top Performers', {
            'fields': ('most_booked_tour', 'most_booked_tour_count', 'highest_rated_tour', 'highest_rated_tour_rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )