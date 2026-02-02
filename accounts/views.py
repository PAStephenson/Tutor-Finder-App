from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.urls import reverse, reverse_lazy

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import Subject

CustomUser = get_user_model()

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('profile')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')
        return response

def home(request):
    return render(request, 'home.html')

@login_required
def profile(request):
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=request.user)

    if request.user.documents_approved:
        if 'qts_certificate' in form.fields:
            del form.fields['qts_certificate']
        if 'dbs_certificate' in form.fields:
            del form.fields['dbs_certificate']

    if request.user.references_approved:
        if 'referee1_name' in form.fields:
            del form.fields['referee1_name']
        if 'referee1_email' in form.fields:
            del form.fields['referee1_email']
        if 'referee2_name' in form.fields:
            del form.fields['referee2_name']
        if 'referee2_email' in form.fields:
            del form.fields['referee2_email']

    return render(request, 'edit_profile.html', {'form': form})

def custom_logout_view(request):
    logout(request)
    return redirect('home')
