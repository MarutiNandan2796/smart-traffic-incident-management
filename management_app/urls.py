from django.contrib.auth import views as auth_views
from django.urls import path

from . import forms, views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(authentication_form=forms.LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accidents/', views.accident_list, name='accident_list'),
    path('accidents/new/', views.accident_create, name='accident_create'),
    path('accidents/export/csv/', views.export_accidents_csv, name='export_accidents_csv'),
    path('accidents/<int:pk>/', views.accident_detail, name='accident_detail'),
    path('accidents/<int:pk>/edit/', views.accident_update, name='accident_update'),
    path('accidents/<int:pk>/status/', views.accident_status_update, name='accident_status_update'),
    path('accidents/<int:pk>/delete/', views.accident_delete, name='accident_delete'),
    path('congestion/', views.congestion_list, name='congestion_list'),
    path('congestion/new/', views.congestion_create, name='congestion_create'),
    path('congestion/export/csv/', views.export_congestion_csv, name='export_congestion_csv'),
    path('congestion/<int:pk>/delete/', views.congestion_delete, name='congestion_delete'),
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/new/', views.alert_create, name='alert_create'),
    path('alerts/<int:pk>/toggle/', views.alert_toggle, name='alert_toggle'),
    path('hotspots/', views.hotspot_view, name='hotspots'),
    path('hotspots/export/csv/', views.export_hotspots_csv, name='export_hotspots_csv'),
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/map-data/', views.api_map_data, name='api_map_data'),
    path('api/gemini/status/', views.api_gemini_status, name='api_gemini_status'),
    path('api/gemini/accident/<int:pk>/', views.api_gemini_analyze_accident, name='api_gemini_analyze_accident'),
    path('api/gemini/copilot/', views.api_gemini_copilot, name='api_gemini_copilot'),
    path('api/gemini/save-key/', views.api_gemini_save_key, name='api_gemini_save_key'),
    path('profile/', views.profile, name='profile'),
    path('profile/password/', views.change_password, name='change_password'),
]
