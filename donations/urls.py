from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs...
    path('', views.home, name='home'),
    path('donations/', views.donation_list, name='donation_list'),
    path('donations/create/', views.create_donation, name='create_donation'),
    path('donations/<int:pk>/', views.donation_detail, name='donation_detail'),  # This line is crucial
    path('my-donations/', views.my_donations, name='my_donations'),
    path('donations/<int:donation_id>/requests/', views.donation_requests, name='donation_requests'),
    path('requests/<int:request_id>/<str:status>/', views.update_request_status, name='update_request_status'),
    path('setup-donor-profile/', views.setup_donor_profile, name='setup_donor_profile'),
    path('update-donor-profile/', views.update_donor_profile, name='update_donor_profile'),
    
    # New Help Seeker URLs
    path('register-help-seeker/', views.register_help_seeker, name='register_help_seeker'),
    path('help-seeker-dashboard/', views.help_seeker_dashboard, name='help_seeker_dashboard'),
    path('create-help-request/', views.create_help_request, name='create_help_request'),
    path('help-seekers/', views.help_seeker_directory, name='help_seeker_directory'),
    path('help-seekers/map/', views.public_help_seekers_map, name='public_help_seekers_map'),
    
    # Donation Matching URLs
    path('donations/<int:donation_id>/nearby-help-seekers/', views.nearby_help_seekers, name='nearby_help_seekers'),
    path('donation-match/<int:donation_id>/<int:seeker_id>/', views.create_donation_match, name='create_donation_match'),
    path('donation-matches/<int:match_id>/', views.donation_match_detail, name='donation_match_detail'),

    # Add these to urlpatterns
path('verification/donor/', views.submit_donor_verification, name='submit_donor_verification'),
path('verification/help-seeker/', views.submit_help_seeker_verification, name='submit_help_seeker_verification'),
path('verification/status/', views.verification_status, name='verification_status'),
path('admin/verification/', views.admin_verification_dashboard, name='admin_verification_dashboard'),
path('admin/verification/<int:request_id>/', views.review_verification, name='review_verification'),



    
    # Superuser verification panel URLs
    path('superuser/verification-panel/', views.superuser_verification_panel, name='superuser_verification_panel'),
    path('superuser/verify/<str:profile_type>/<int:profile_id>/', views.verify_profile, name='verify_profile'),
    path('superuser/reject/<str:profile_type>/<int:profile_id>/', views.reject_profile, name='reject_profile'),
    path('superuser/delete/<str:profile_type>/<int:profile_id>/', views.delete_profile, name='delete_profile'),
    path('superuser/bulk-verify/', views.bulk_verify_profiles, name='bulk_verify_profiles'),
    path('superuser/bulk-delete/', views.bulk_delete_profiles, name='bulk_delete_profiles'),
]

