from django.urls import path
from .views import (
    SignUpView,
    home,
    profile,
    edit_profile,
    custom_logout_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('logout/', custom_logout_view, name='custom_logout'), # Use unique name
]
