from django.urls import path
from .views import Login, update_profile, user_list_create, user_detail
urlpatterns = [
    path('login/', Login, name='login'),
    path('update_profile/<str:pk>/', update_profile, name='update_profile'),
    path('users/', user_list_create, name='user_list_create'),
    path('users/<str:pk>/', user_detail, name='user_detail'),
]
