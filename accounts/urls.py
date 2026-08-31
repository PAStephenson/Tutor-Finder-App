from django.urls import path
from .views import (
    SignUpView,
    ParentSignUpView,
    RoleAwareLoginView,
    home,
    profile,
    edit_profile,
    tutor_search,
    tutor_detail,
    conversation_detail,
    message_inbox,
    news_list,
    custom_logout_view,
)

urlpatterns = [
    path('', home, name='home'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signup/parent/', ParentSignUpView.as_view(), name='parent_signup'),
    path('accounts/login/', RoleAwareLoginView.as_view(), name='login'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('tutors/', tutor_search, name='tutor_search'),
    path('tutors/<int:pk>/', tutor_detail, name='tutor_detail'),
    path('messages/', message_inbox, name='message_inbox'),
    path('messages/<int:pk>/', conversation_detail, name='conversation_detail'),
    path('news/', news_list, name='news_list'),
    path('logout/', custom_logout_view, name='custom_logout'), # Use unique name
]
