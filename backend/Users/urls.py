from django.urls import path
from .views import Login, update_profile
urlpatterns = [
    path('login/', Login, name='login'),
    path('update_profile/<str:pk>/', update_profile, name='update_profile'),
]
