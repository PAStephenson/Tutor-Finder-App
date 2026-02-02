from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms.widgets import DateInput
from .models import CustomUser, Subject, SubjectLevel

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text="Your password must contain at least 8 characters.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

    date_of_birth = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False 
    )
    
    terms_agreed = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the terms to sign up.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'agreementCheckbox'})
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'date_of_birth')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class CustomUserChangeForm(UserChangeForm):
    password = None 
    
    date_of_birth = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select subject-select'}),
        required=False
    )
    subject_levels = forms.ModelMultipleChoiceField(
        queryset=SubjectLevel.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select subject-level-select'}),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = (
            'profile_picture',
            'first_name', 'last_name', 'email', 'date_of_birth', 
            'bio',
            'cost', 'subjects', 'subject_levels',
            'qts_certificate', 'dbs_certificate',
            'referee1_name', 'referee1_email', 'referee2_name', 'referee2_email',
        )
        exclude = (
            'password', 'is_staff', 'is_superuser', 'is_active', 
            'groups', 'user_permissions', 'last_login', 'date_joined', 
            'documents_approved', 'references_approved', 
            'id_check_completed'
        )
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'maxlength': 1500}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'qts_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'dbs_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'referee1_name': forms.TextInput(attrs={'class': 'form-control'}),
            'referee1_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'referee2_name': forms.TextInput(attrs={'class': 'form-control'}),
            'referee2_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['bio'].required = False
        self.fields['cost'].required = False
        self.fields['subjects'].required = False
        self.fields['subject_levels'].required = False
        self.fields['qts_certificate'].required = False
        self.fields['dbs_certificate'].required = False
        self.fields['referee1_name'].required = False
        self.fields['referee1_email'].required = False
        self.fields['referee2_name'].required = False
        self.fields['referee2_email'].required = False
        
        if self.instance.pk:
            if self.instance.documents_approved:
                if 'qts_certificate' in self.fields: del self.fields['qts_certificate']
                if 'dbs_certificate' in self.fields: del self.fields['dbs_certificate']
            
            if self.instance.references_approved:
                fields_to_remove = ['referee1_name', 'referee1_email', 'referee2_name', 'referee2_email']
                for field in fields_to_remove:
                    if field in self.fields:
                        del self.fields[field]
