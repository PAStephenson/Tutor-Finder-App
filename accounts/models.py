from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import uuid
import os

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents/', filename)

def get_profile_pic_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('profile_pics/', filename)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class SubjectLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    profile_picture = models.ImageField(upload_to=get_profile_pic_path, null=True, blank=True)
    
    bio = models.TextField(max_length=1500, blank=True, help_text="A short bio about yourself (max 1500 characters).")

    cost = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Cost per hour in £")
    subjects = models.ManyToManyField(Subject, blank=True, related_name="tutors")
    subject_levels = models.ManyToManyField(SubjectLevel, blank=True, related_name="tutors")

    qts_certificate = models.FileField(upload_to=get_file_path, null=True, blank=True)
    dbs_certificate = models.FileField(upload_to=get_file_path, null=True, blank=True)
    documents_approved = models.BooleanField(default=False)

    referee1_name = models.CharField(max_length=200, blank=True)
    referee1_email = models.EmailField(max_length=200, blank=True)
    referee2_name = models.CharField(max_length=200, blank=True)
    referee2_email = models.EmailField(max_length=200, blank=True)
    references_approved = models.BooleanField(default=False)
    
    id_check_completed = models.BooleanField(default=False, verbose_name="ID Check Completed")
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_profile_complete(self):
        if not self.documents_approved: return False
        if not self.references_approved: return False
        if not self.id_check_completed: return False
        if not self.cost: return False
        if not self.subjects.exists(): return False
        if not self.subject_levels.exists(): return False
        return True
