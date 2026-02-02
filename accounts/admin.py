from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, Subject, SubjectLevel

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    
    list_display = (
        'email', 'first_name', 'last_name', 'is_staff', 
        'documents_approved', 'references_approved', 'id_check_completed'
    )
    
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'documents_approved', 'references_approved', 'id_check_completed') 
    
    def view_profile_picture(self, obj):
        if obj.profile_picture:
            url = obj.profile_picture.url
            return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 100px; max-width: 100px; border-radius: 50%; object-fit: cover; border: 2px solid #ccc;" /></a>', url)
        return "No profile picture"
    view_profile_picture.short_description = "Profile Pic"

    def view_qts_certificate(self, obj):
        if obj.qts_certificate:
            url = obj.qts_certificate.url
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px; border: 1px solid #ccc;" /></a><br><a href="{0}" target="_blank">View Full Image</a>', url)
            return format_html('<a href="{}" target="_blank">View Document</a>', url)
        return "Not uploaded"
    view_qts_certificate.short_description = "QTS Preview"

    def view_dbs_certificate(self, obj):
        if obj.dbs_certificate:
            url = obj.dbs_certificate.url
            if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height: 150px; border: 1px solid #ccc;" /></a><br><a href="{0}" target="_blank">View Full Image</a>', url)
            return format_html('<a href="{}" target="_blank">View Document</a>', url)
        return "Not uploaded"
    view_dbs_certificate.short_description = "DBS Preview"

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'profile_picture', 'view_profile_picture',
                'first_name', 'last_name', 'date_of_birth',
                'bio'
            )
        }),
        ('Tutoring Details', {'fields': ('cost', 'subjects', 'subject_levels')}),
        ('Documents', {'fields': (
            'qts_certificate', 'view_qts_certificate', 
            'dbs_certificate', 'view_dbs_certificate', 
            'documents_approved'
        )}),
        ('References', {'fields': ('referee1_name', 'referee1_email', 'referee2_name', 'referee2_email', 'references_approved')}),
        ('ID Check', {'fields': ('id_check_completed',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('view_profile_picture', 'view_qts_certificate', 'view_dbs_certificate')
    filter_horizontal = ('subjects', 'subject_levels', 'groups', 'user_permissions',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subject)
admin.site.register(SubjectLevel)
