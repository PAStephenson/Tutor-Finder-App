from django.conf import settings

def parent_signup_flag(request):
    return {'parent_signup_enabled': not settings.HIDE_PARENT_SIGNUP}
