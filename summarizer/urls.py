from django.contrib import admin
from django.urls import path
from summarizer import views

urlpatterns = [
    path('', views.home, name='home'),
    path('history/', views.history, name='history'),
    path('api/analyze/', views.AnalyzeAPI.as_view(), name='api_analyze'),
    path('api/search/', views.SearchAPI.as_view(), name='api_search'),
]
