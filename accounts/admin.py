from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .forms import AdminUserCreationForm, AdminUserChangeForm
from .models import CustomUser, Subject, SubjectLevel, Conversation, Message, NewsPost, TokenPurchase, ContactUnlock

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = (
        'email', 'first_name', 'last_name', 'role', 'is_staff',
        'documents_approved', 'references_approved', 'id_check_completed', 'welcome_email_sent', 'token_balance'
    )
    list_editable = ('welcome_email_sent',)

    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'documents_approved', 'references_approved', 'id_check_completed', 'welcome_email_sent')
    
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
        (None, {'fields': ('email', 'password', 'role')}),
        ('Personal Info', {
            'fields': (
                'profile_picture', 'view_profile_picture',
                'first_name', 'last_name', 'date_of_birth',
                'bio', 'phone_number'
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
        ('Onboarding Emails (Admin Only)', {'fields': ('welcome_email_sent',)}),
        ('Tokens', {'fields': ('token_balance',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('view_profile_picture', 'view_qts_certificate', 'view_dbs_certificate')
    filter_horizontal = ('subjects', 'subject_levels', 'groups', 'user_permissions',)

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'body', 'created_at')
    can_delete = False

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'tutor', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'parent__email', 'parent__first_name', 'parent__last_name',
        'tutor__email', 'tutor__first_name', 'tutor__last_name',
    )
    readonly_fields = ('tutor', 'parent', 'created_at')
    inlines = [MessageInline]

class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at')
    date_hierarchy = 'published_at'
    search_fields = ('title', 'body')
    ordering = ('-published_at',)

class TokenPurchaseAdmin(admin.ModelAdmin):
    list_display = ('parent', 'tokens', 'amount_pence', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('parent__email', 'stripe_checkout_session_id')
    readonly_fields = ('parent', 'tokens', 'amount_pence', 'status', 'stripe_checkout_session_id', 'created_at', 'completed_at')

class ContactUnlockAdmin(admin.ModelAdmin):
    list_display = ('parent', 'tutor', 'unlocked_at')
    list_filter = ('unlocked_at',)
    search_fields = (
        'parent__email', 'parent__first_name', 'parent__last_name',
        'tutor__email', 'tutor__first_name', 'tutor__last_name',
    )
    readonly_fields = ('parent', 'tutor', 'unlocked_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subject)
admin.site.register(SubjectLevel)
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(NewsPost, NewsPostAdmin)
admin.site.register(TokenPurchase, TokenPurchaseAdmin)
admin.site.register(ContactUnlock, ContactUnlockAdmin)
