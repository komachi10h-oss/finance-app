from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import CustomLoginView,verify_otp

app_name = 'users'  # <- importante

urlpatterns = [
    path('', views.users, name='users'),
    path('register/', views.register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='users:login'), name='logout'),
    path("verify-otp/", verify_otp, name="verify_otp"),
]
