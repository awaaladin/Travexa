# from django.urls import path
# from . import views

# urlpatterns = [
#     path('register/', views.register_view, name='register'),
#     path('login/', views.login_view, name='login'),
#     path('logout/', views.logout_view, name='logout'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('users/', views.user_list, name='user_list'),
#     path('tours/', views.tour_list, name='tour_list'),
#     path('bookings/', views.booking_list, name='booking_list'),
#     path('payments/', views.payment_list, name='payment_list'),
#     path('reviews/', views.review_list, name='review_list'),
#     path('reports/', views.report_view, name='report_view'),
#     path('settings/', views.settings_view, name='settings'),
# ]
from django.urls import path
from . import views

urlpatterns = [
    # Home and Tour URLs
    path('', views.home, name='home'),
    path('tours/', views.tour_list, name='tour_list'),
    path('tours/<int:tour_id>/', views.tour_detail, name='tour_detail'),
    path('tours/<int:tour_id>/map/', views.tour_map, name='tour_map'),

    # Authentication URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/verify/<str:email>/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/<str:email>/<str:otp>/', views.password_reset_confirm, name='password_reset_confirm'),

    # Profile URLs
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),

    # Booking URLs
    path('tours/<int:tour_id>/book/', views.booking_create, name='booking_create'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<uuid:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<uuid:booking_id>/cancel/', views.booking_cancel, name='booking_cancel'),

    # Payment URLs
    path('bookings/<uuid:booking_id>/payment/', views.payment_create, name='payment_create'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),

    # API URLs
    path('api/tours/<int:tour_id>/dates/', views.get_available_dates, name='get_available_dates'),
]