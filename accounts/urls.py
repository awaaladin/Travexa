from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('landing/', views.landing_page, name='landing_page'),
    # Public URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),    
    path('register/', views.register_view, name='register'),
    path('password-reset/', views.password_reset, name='password_reset'),
    
    # User Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),  # Changed from user_dashboard
    path('user/', views.user, name='user'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # Tour URLs
    path('tours/', views.tour_list, name='tour_list'),
    path('tours/<int:tour_id>/', views.tour_detail, name='tour_detail'),
    path('tours/<int:tour_id>/book/', views.booking_create, name='booking_create'),
    path('tours/<int:tour_id>/review/', views.review_create, name='review_create'),
    
    # Booking URLs
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<uuid:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<uuid:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),
    path('bookings/<uuid:booking_id>/payment/', views.payment_create, name='payment_create'),
    
    # Admin URLs
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/activity/', views.admin_activity_log, name='admin_activity_log'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),
    path('admin/users/', views.admin_user_list, name='admin_user_list'),
    path('admin/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin/tours/', views.admin_tour_list, name='admin_tour_list'),
    path('admin/tours/create/', views.admin_tour_create, name='admin_tour_create'),
    path('admin/tours/<int:tour_id>/', views.admin_tour_detail, name='admin_tour_detail'),
    path('admin/reports/', views.admin_report_list, name='admin_report_list'),
    path('admin/reports/create/', views.admin_report_create, name='admin_report_create'),
    path('admin/reports/<int:report_id>/', views.admin_report_detail, name='admin_report_detail'),
    
    # API URLs for admin dashboard
    path('api/stats/bookings/', views.api_booking_stats, name='api_booking_stats'),
    path('api/stats/revenue/', views.api_revenue_stats, name='api_revenue_stats'),
    path('api/stats/users/', views.api_user_stats, name='api_user_stats'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
      # Process payment
    path('process-payment/<int:booking_id>/', views.process_payment, name='process_payment'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('reviews/respond/', views.respond_to_reviews, name='respond_to_reviews'),
    path('reviews/user/', views.user_reviews, name='user_reviews'),
    path('travel-history/', views.travel_history, name='travel_history'),
    path('tour-area-map/', views.tour_area_map, name='tour_area_map'),
    path('support/', views.support, name='support'),
]