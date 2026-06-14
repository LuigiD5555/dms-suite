from django.urls import path
from users.views import (
    HomeView, LoginView, RegisterView, ForgetPasswordView,
    ChangePasswordView, LogoutView, UsersView, UserHistoryView,
    CustomUserProfileView
)

urlpatterns = [
    # path('', TemplateView.as_view(template_name='index.html'))
    path('', HomeView.as_view(), name="home"),
    path('login/', LoginView.as_view(), name="login"),
    path('register/', RegisterView.as_view(), name="register"),
    path('forget-password/', ForgetPasswordView.as_view(), name="forget_password"),
    path('change-password/<token>/', ChangePasswordView.as_view(), name="change_password"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('users/', UsersView.as_view(), name='users'),
    path('users/<int:pk>/history/', UserHistoryView.as_view(), name="history"),
    path('users/<int:pk>/change/', CustomUserProfileView.as_view(), name="profile"),
]
