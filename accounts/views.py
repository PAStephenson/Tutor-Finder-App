from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import CustomUserCreationForm, CustomUserChangeForm, ParentSignUpForm, MessageForm
from .models import Subject, SubjectLevel, Conversation, Message, NewsPost

CustomUser = get_user_model()

APPROVED_TUTOR_FILTERS = dict(
    is_active=True,
    is_staff=False,
    role=CustomUser.ROLE_TUTOR,
    documents_approved=True,
    references_approved=True,
    id_check_completed=True,
)

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('profile')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')
        return response

class ParentSignUpView(CreateView):
    form_class = ParentSignUpForm
    success_url = reverse_lazy('tutor_search')
    template_name = 'registration/parent_signup.html'

    def dispatch(self, request, *args, **kwargs):
        if settings.HIDE_PARENT_SIGNUP:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend='django.contrib.auth.backends.ModelBackend')
        return response

class RoleAwareLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        if self.request.user.is_parent:
            return reverse('tutor_search')
        return reverse('profile')

def home(request):
    latest_news = NewsPost.objects.all()[:3]
    return render(request, 'home.html', {'latest_news': latest_news})

def news_list(request):
    news_posts = NewsPost.objects.all()
    return render(request, 'news_list.html', {'news_posts': news_posts})

@login_required
def profile(request):
    if request.user.is_parent:
        return redirect('tutor_search')
    return render(request, 'profile.html')

@login_required
def edit_profile(request):
    if request.user.is_parent:
        return redirect('tutor_search')
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

@login_required
def tutor_search(request):
    tutors = CustomUser.objects.filter(
        **APPROVED_TUTOR_FILTERS, cost__isnull=False
    ).exclude(subjects__isnull=True).exclude(subject_levels__isnull=True).distinct()

    subject_id = request.GET.get('subject', '')
    level_id = request.GET.get('level', '')
    max_price = request.GET.get('max_price', '')
    query = request.GET.get('q', '')

    if subject_id:
        tutors = tutors.filter(subjects__id=subject_id)
    if level_id:
        tutors = tutors.filter(subject_levels__id=level_id)
    if max_price:
        try:
            tutors = tutors.filter(cost__lte=Decimal(max_price))
        except InvalidOperation:
            messages.error(request, 'Please enter a valid maximum price.')
    if query:
        tutors = tutors.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(bio__icontains=query)
        )

    tutors = tutors.order_by('cost')

    paginator = Paginator(tutors, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'subjects': Subject.objects.all().order_by('name'),
        'levels': SubjectLevel.objects.all().order_by('name'),
        'selected_subject': subject_id,
        'selected_level': level_id,
        'max_price': max_price,
        'query': query,
    }
    return render(request, 'tutor_list.html', context)

@login_required
def tutor_detail(request, pk):
    tutor = get_object_or_404(CustomUser, pk=pk, **APPROVED_TUTOR_FILTERS)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            conversation, _ = Conversation.objects.get_or_create(tutor=tutor, parent=request.user)
            Message.objects.create(
                conversation=conversation,
                sender=Message.SENDER_PARENT,
                body=form.cleaned_data['body'],
            )
            return redirect('conversation_detail', pk=conversation.pk)
    else:
        form = MessageForm()

    return render(request, 'tutor_detail.html', {'tutor': tutor, 'form': form})

@login_required
def message_inbox(request):
    conversations = Conversation.objects.filter(Q(tutor=request.user) | Q(parent=request.user))
    return render(request, 'message_inbox.html', {'conversations': conversations})

@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(
        Conversation, Q(pk=pk) & (Q(tutor=request.user) | Q(parent=request.user))
    )
    viewer = Message.SENDER_TUTOR if conversation.tutor_id == request.user.id else Message.SENDER_PARENT

    if request.method == 'POST':
        reply_form = MessageForm(request.POST)
        if reply_form.is_valid():
            Message.objects.create(
                conversation=conversation,
                sender=viewer,
                body=reply_form.cleaned_data['body'],
            )
            return redirect('conversation_detail', pk=pk)
    else:
        reply_form = MessageForm()

    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'thread_messages': conversation.messages.all(),
        'form': reply_form,
        'viewer': viewer,
    })

def custom_logout_view(request):
    logout(request)
    return redirect('home')
