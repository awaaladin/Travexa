from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'reporting'

urlpatterns = [
    # Authentication and user management
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard and report generation
    path('dashboard/', login_required(views.dashboard), name='dashboard'),
    path('generate/', views.generate_report, name='generate_report'),
    
    # View specific reports
    path('booking/<int:report_id>/', views.view_booking_report, name='view_booking_report'),
    path('revenue/<int:report_id>/', views.view_revenue_report, name='view_revenue_report'),
    path('user-growth/<int:report_id>/', views.view_user_growth_report, name='user_growth_report'),
    path('tour-performance/<int:report_id>/', views.view_tour_performance_report, name='tour_performance_report'),
    
    # API endpoints for chart data
    path('api/booking-stats/', views.booking_stats_api, name='booking_stats_api'),
    path('api/rating-stats/', views.rating_stats_api, name='rating_stats_api'),
    
    # Report and analytics URLs
    path('tours/<int:tour_id>/analytics/', views.tour_review_analytics, name='tour_review_analytics'),
    path('my-review-stats/', views.user_review_stats, name='user_review_stats'),
    path('top-rated-tours/', views.top_rated_tours, name='top_rated_tours'),
    path('api/tours/<int:tour_id>/review-data/', views.get_review_data_json, name='get_review_data_json'),
    
    # Tour detail view that includes reviews
    path('tours/<int:tour_id>/', views.tour_detail, name='tour_detail'),
    
    # Review management
    path('tours/<int:tour_id>/add-review/', views.add_review, name='add_review'),
    path('reviews/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/<int:review_id>/respond/', views.respond_to_review, name='respond_to_review'),
    
    # User reviews dashboard
    path('my-reviews/', views.user_reviews, name='user_reviews'),
    
    # Additional review management
    path('create/<int:booking_id>/', views.create_review, name='create_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('respond/<int:review_id>/', views.respond_to_review, name='respond_to_review'),
    path('tour/<int:tour_id>/', views.tour_reviews, name='tour_reviews'),
]