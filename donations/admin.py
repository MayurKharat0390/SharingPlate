from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import DonorProfile, DonationCategory, Donation, DonationRequest, Notification, Feedback, HelpSeekerType, HelpSeeker, DonationMatch, HelpRequest, Rating, VerificationRequest

# Inline for DonorProfile in User Admin
class DonorProfileInline(admin.StackedInline):
    model = DonorProfile
    can_delete = False
    verbose_name_plural = 'Donor Profile'
    fields = ('organization_name', 'user_type', 'phone', 'address', 'city', 'state', 
              'pincode', 'verification_status', 'verification_document', 'verified_at', 'verified_by')
    readonly_fields = ('verified_at',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

# Inline for HelpSeeker in User Admin
class HelpSeekerInline(admin.StackedInline):
    model = HelpSeeker
    can_delete = False
    verbose_name_plural = 'Help Seeker Profile'
    fields = ('organization_name', 'seeker_type', 'description', 'phone', 'address',
              'city', 'state', 'pincode', 'verification_status', 'verification_document',
              'verified_at', 'verified_by', 'is_urgent', 'urgent_needs')
    readonly_fields = ('verified_at',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_donor_status', 'get_seeker_status', 'is_staff', 'is_active')
    list_filter = ('donorprofile__verification_status', 'helpseeker__verification_status', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    actions = ['activate_users', 'deactivate_users']
    
    def get_donor_status(self, obj):
        if hasattr(obj, 'donorprofile'):
            status = obj.donorprofile.get_verification_status_display()
            color = {
                'verified': 'green',
                'pending': 'orange',
                'rejected': 'red',
                'not_submitted': 'gray'
            }.get(obj.donorprofile.verification_status, 'black')
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
        return format_html('<span style="color: gray;">No Profile</span>')
    get_donor_status.short_description = 'Donor Status'
    
    def get_seeker_status(self, obj):
        if hasattr(obj, 'helpseeker'):
            status = obj.helpseeker.get_verification_status_display()
            color = {
                'verified': 'green',
                'pending': 'orange',
                'rejected': 'red'
            }.get(obj.helpseeker.verification_status, 'black')
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, status)
        return format_html('<span style="color: gray;">No Profile</span>')
    get_seeker_status.short_description = 'Seeker Status'

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = "Deactivate selected users"

    def get_inlines(self, request, obj=None):
        if obj:
            inlines = []
            if hasattr(obj, 'donorprofile'):
                inlines.append(DonorProfileInline)
            if hasattr(obj, 'helpseeker'):
                inlines.append(HelpSeekerInline)
            return inlines
        return []

# Unregister default User admin and register custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'verification_type', 'get_status_badge', 'submitted_at', 'reviewed_at', 'reviewed_by', 'quick_actions']
    list_filter = ['verification_type', 'status', 'submitted_at']
    search_fields = ['user__username', 'user__email', 'notes']
    readonly_fields = ['submitted_at', 'reviewed_at']
    list_per_page = 20
    actions = ['approve_requests', 'reject_requests', 'mark_under_review', 'mark_needs_info']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'verification_type', 'document')
        }),
        ('Verification Details', {
            'fields': ('status', 'notes')
        }),
        ('Review Information', {
            'fields': ('submitted_at', 'reviewed_at', 'reviewed_by'),
            'classes': ('collapse',)
        }),
    )

    def get_status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'under_review': '#17a2b8',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'needs_more_info': '#fd7e14'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'

    def quick_actions(self, obj):
        if obj.status in ['pending', 'under_review', 'needs_more_info']:
            return format_html(
                '<div style="display: flex; gap: 5px;">'
                '<a href="{}" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Approve</a>'
                '<a href="{}" style="background: #dc3545; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Reject</a>'
                '</div>',
                f"{obj.pk}/approve/",
                f"{obj.pk}/reject/"
            )
        return '-'
    quick_actions.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/approve/', self.admin_site.admin_view(self.approve_verification), name='verification_request_approve'),
            path('<path:object_id>/reject/', self.admin_site.admin_view(self.reject_verification), name='verification_request_reject'),
        ]
        return custom_urls + urls

    def approve_verification(self, request, object_id):
        try:
            vr = VerificationRequest.objects.get(pk=object_id)
            vr.status = 'approved'
            vr.reviewed_at = timezone.now()
            vr.reviewed_by = request.user
            vr.save()
            
            # Update corresponding profile
            if vr.verification_type == 'donor' and hasattr(vr.user, 'donorprofile'):
                donor_profile = vr.user.donorprofile
                donor_profile.verification_status = 'verified'
                donor_profile.verified_at = timezone.now()
                donor_profile.verified_by = request.user
                donor_profile.save()
                
            elif vr.verification_type == 'help_seeker' and hasattr(vr.user, 'helpseeker'):
                seeker_profile = vr.user.helpseeker
                seeker_profile.verification_status = 'verified'
                seeker_profile.verified_at = timezone.now()
                seeker_profile.verified_by = request.user
                seeker_profile.save()
                
            messages.success(request, f'Verification request for {vr.user.username} has been approved.')
        except VerificationRequest.DoesNotExist:
            messages.error(request, 'Verification request not found.')
        
        return HttpResponseRedirect(reverse('admin:donations_verificationrequest_changelist'))

    def reject_verification(self, request, object_id):
        try:
            vr = VerificationRequest.objects.get(pk=object_id)
            vr.status = 'rejected'
            vr.reviewed_at = timezone.now()
            vr.reviewed_by = request.user
            vr.save()
            messages.success(request, f'Verification request for {vr.user.username} has been rejected.')
        except VerificationRequest.DoesNotExist:
            messages.error(request, 'Verification request not found.')
        
        return HttpResponseRedirect(reverse('admin:donations_verificationrequest_changelist'))

    def approve_requests(self, request, queryset):
        for vr in queryset:
            vr.status = 'approved'
            vr.reviewed_at = timezone.now()
            vr.reviewed_by = request.user
            vr.save()
            
            if vr.verification_type == 'donor' and hasattr(vr.user, 'donorprofile'):
                vr.user.donorprofile.verification_status = 'verified'
                vr.user.donorprofile.verified_at = timezone.now()
                vr.user.donorprofile.verified_by = request.user
                vr.user.donorprofile.save()
            elif vr.verification_type == 'help_seeker' and hasattr(vr.user, 'helpseeker'):
                vr.user.helpseeker.verification_status = 'verified'
                vr.user.helpseeker.verified_at = timezone.now()
                vr.user.helpseeker.verified_by = request.user
                vr.user.helpseeker.save()
                
        self.message_user(request, f'{queryset.count()} verification requests approved successfully.')
    approve_requests.short_description = "✅ Approve selected requests"

    def reject_requests(self, request, queryset):
        for vr in queryset:
            vr.status = 'rejected'
            vr.reviewed_at = timezone.now()
            vr.reviewed_by = request.user
            vr.save()
        self.message_user(request, f'{queryset.count()} verification requests rejected.')
    reject_requests.short_description = "❌ Reject selected requests"

    def mark_under_review(self, request, queryset):
        queryset.update(status='under_review')
        self.message_user(request, f'{queryset.count()} verification requests marked as under review.')
    mark_under_review.short_description = "🔍 Mark as under review"

    def mark_needs_info(self, request, queryset):
        queryset.update(status='needs_more_info')
        self.message_user(request, f'{queryset.count()} verification requests marked as needs more information.')
    mark_needs_info.short_description = "📋 Mark as needs more info"

@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization_name', 'user_type', 'get_verification_badge', 'city', 'state', 'verified_at', 'quick_actions']
    list_filter = ['user_type', 'verification_status', 'city', 'state']
    search_fields = ['user__username', 'organization_name', 'city', 'state', 'phone']
    readonly_fields = ['created_at', 'verified_at']
    list_per_page = 20
    actions = ['verify_donors', 'reject_donors', 'mark_pending']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'organization_name', 'user_type')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address', 'city', 'state', 'pincode')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verification_document', 'verified_at', 'verified_by')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_verification_badge(self, obj):
        status_colors = {
            'verified': '#28a745',
            'pending': '#ffc107',
            'rejected': '#dc3545',
            'not_submitted': '#6c757d'
        }
        color = status_colors.get(obj.verification_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_verification_status_display()
        )
    get_verification_badge.short_description = 'Verification Status'

    def quick_actions(self, obj):
        if obj.verification_status != 'verified':
            return format_html(
                '<a href="{}" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Verify</a>',
                f"{obj.pk}/verify/"
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">✓ Verified</span>'
        )
    quick_actions.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/verify/', self.admin_site.admin_view(self.verify_donor), name='donorprofile_verify'),
        ]
        return custom_urls + urls

    def verify_donor(self, request, object_id):
        try:
            donor = DonorProfile.objects.get(pk=object_id)
            donor.verification_status = 'verified'
            donor.verified_at = timezone.now()
            donor.verified_by = request.user
            donor.save()
            messages.success(request, f'Donor {donor.user.username} has been verified successfully.')
        except DonorProfile.DoesNotExist:
            messages.error(request, 'Donor profile not found.')
        
        return HttpResponseRedirect(reverse('admin:donations_donorprofile_changelist'))

    def verify_donors(self, request, queryset):
        for donor in queryset:
            donor.verification_status = 'verified'
            donor.verified_at = timezone.now()
            donor.verified_by = request.user
            donor.save()
        self.message_user(request, f'{queryset.count()} donors verified successfully.')
    verify_donors.short_description = "✅ Verify selected donors"

    def reject_donors(self, request, queryset):
        queryset.update(verification_status='rejected', verified_at=None, verified_by=None)
        self.message_user(request, f'{queryset.count()} donors rejected.')
    reject_donors.short_description = "❌ Reject selected donors"

    def mark_pending(self, request, queryset):
        queryset.update(verification_status='pending', verified_at=None, verified_by=None)
        self.message_user(request, f'{queryset.count()} donors marked as pending.')
    mark_pending.short_description = "⏳ Mark as pending"

@admin.register(HelpSeeker)
class HelpSeekerAdmin(admin.ModelAdmin):
    list_display = ['organization_name', 'seeker_type', 'get_verification_badge', 'city', 'state', 'is_urgent', 'verified_at', 'quick_actions']
    list_filter = ['seeker_type', 'verification_status', 'city', 'state', 'is_urgent']
    search_fields = ['organization_name', 'city', 'description', 'phone', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    list_per_page = 20
    actions = ['verify_seekers', 'reject_seekers', 'mark_pending', 'mark_urgent', 'mark_not_urgent']
    
    fieldsets = (
        ('Organization Information', {
            'fields': ('user', 'organization_name', 'seeker_type', 'description')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address', 'city', 'state', 'pincode', 'latitude', 'longitude')
        }),
        ('Capacity & Urgency', {
            'fields': ('capacity', 'is_urgent', 'urgent_needs')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verification_document', 'verified_at', 'verified_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_verification_badge(self, obj):
        status_colors = {
            'verified': '#28a745',
            'pending': '#ffc107',
            'rejected': '#dc3545'
        }
        color = status_colors.get(obj.verification_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_verification_status_display()
        )
    get_verification_badge.short_description = 'Verification Status'

    def quick_actions(self, obj):
        if obj.verification_status != 'verified':
            return format_html(
                '<a href="{}" style="background: #28a745; color: white; padding: 4px 8px; text-decoration: none; border-radius: 3px; font-size: 12px;">Verify</a>',
                f"{obj.pk}/verify/"
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">✓ Verified</span>'
        )
    quick_actions.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/verify/', self.admin_site.admin_view(self.verify_seeker), name='helpseeker_verify'),
        ]
        return custom_urls + urls

    def verify_seeker(self, request, object_id):
        try:
            seeker = HelpSeeker.objects.get(pk=object_id)
            seeker.verification_status = 'verified'
            seeker.verified_at = timezone.now()
            seeker.verified_by = request.user
            seeker.save()
            messages.success(request, f'Help seeker {seeker.organization_name} has been verified successfully.')
        except HelpSeeker.DoesNotExist:
            messages.error(request, 'Help seeker not found.')
        
        return HttpResponseRedirect(reverse('admin:donations_helpseeker_changelist'))

    def verify_seekers(self, request, queryset):
        for seeker in queryset:
            seeker.verification_status = 'verified'
            seeker.verified_at = timezone.now()
            seeker.verified_by = request.user
            seeker.save()
        self.message_user(request, f'{queryset.count()} help seekers verified successfully.')
    verify_seekers.short_description = "✅ Verify selected help seekers"

    def reject_seekers(self, request, queryset):
        queryset.update(verification_status='rejected', verified_at=None, verified_by=None)
        self.message_user(request, f'{queryset.count()} help seekers rejected.')
    reject_seekers.short_description = "❌ Reject selected help seekers"

    def mark_pending(self, request, queryset):
        queryset.update(verification_status='pending', verified_at=None, verified_by=None)
        self.message_user(request, f'{queryset.count()} help seekers marked as pending.')
    mark_pending.short_description = "⏳ Mark as pending"

    def mark_urgent(self, request, queryset):
        queryset.update(is_urgent=True)
        self.message_user(request, f'{queryset.count()} help seekers marked as urgent.')
    mark_urgent.short_description = "🚨 Mark as urgent"

    def mark_not_urgent(self, request, queryset):
        queryset.update(is_urgent=False)
        self.message_user(request, f'{queryset.count()} help seekers marked as not urgent.')
    mark_not_urgent.short_description = "✅ Mark as not urgent"

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['title', 'donor', 'category', 'status', 'quantity', 'pickup_city', 'pickup_deadline', 'created_at']
    list_filter = ['category', 'status', 'food_type', 'created_at']
    search_fields = ['title', 'description', 'donor__user__username', 'pickup_city']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20

@admin.register(DonationCategory)
class DonationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

@admin.register(HelpSeekerType)
class HelpSeekerTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

# Register other models with basic admin
@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ['donation', 'requester', 'status', 'requested_quantity', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at']

@admin.register(DonationMatch)
class DonationMatchAdmin(admin.ModelAdmin):
    list_display = ['donation', 'help_seeker', 'status', 'distance_km', 'match_score', 'created_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at']

@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'help_seeker', 'category', 'urgency', 'is_active', 'created_at']
    list_filter = ['urgency', 'is_active', 'category']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'donation', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['donor', 'help_seeker', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    readonly_fields = ['created_at']