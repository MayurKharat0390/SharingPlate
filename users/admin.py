from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from django.utils import timezone

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('phone', 'address', 'city', 'state', 'pincode', 'is_volunteer', 'volunteer_skills', 'is_verified', 'verified_at', 'verification_notes')
    readonly_fields = ('verified_at',)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_is_verified', 'get_is_volunteer', 'is_staff')
    list_filter = ('userprofile__is_verified', 'userprofile__is_volunteer', 'is_staff', 'is_active')
    
    def get_is_verified(self, obj):
        return obj.userprofile.is_verified
    get_is_verified.boolean = True
    get_is_verified.short_description = 'Verified'
    
    def get_is_volunteer(self, obj):
        return obj.userprofile.is_volunteer
    get_is_volunteer.boolean = True
    get_is_volunteer.short_description = 'Volunteer'

# Unregister the default User admin and register with custom admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city', 'state', 'is_verified', 'is_volunteer', 'verified_at')
    list_filter = ('is_verified', 'is_volunteer', 'city', 'state')
    search_fields = ('user__username', 'user__email', 'phone', 'city')
    readonly_fields = ('verified_at',)
    actions = ['verify_profiles', 'unverify_profiles']
    
    def verify_profiles(self, request, queryset):
        for profile in queryset:
            profile.is_verified = True
            profile.verified_at = timezone.now()
            profile.save()
        self.message_user(request, f'{queryset.count()} profiles verified successfully.')
    verify_profiles.short_description = "Verify selected profiles"
    
    def unverify_profiles(self, request, queryset):
        queryset.update(is_verified=False, verified_at=None)
        self.message_user(request, f'{queryset.count()} profiles unverified.')
    unverify_profiles.short_description = "Unverify selected profiles"