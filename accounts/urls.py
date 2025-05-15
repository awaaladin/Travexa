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
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', login_required(views.dashboard), name='dashboard'),
]