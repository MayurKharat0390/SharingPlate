from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
import json

from .models import (
    Donation, DonationCategory, DonationRequest, DonorProfile, 
    Notification, HelpSeeker, HelpSeekerType, HelpRequest, 
    DonationMatch, Feedback, Rating, VerificationRequest
)
from .forms import (
    DonationForm, DonationRequestForm, DonorProfileForm,
    HelpSeekerRegistrationForm, HelpRequestForm, DonationMatchForm,
    DonorVerificationForm, HelpSeekerVerificationForm, AdminVerificationForm
)


def home(request):
    """Home page with statistics and recent donations"""
    categories = DonationCategory.objects.all()
    help_seeker_types = HelpSeekerType.objects.all()
    recent_donations = Donation.objects.filter(
        status='available', 
        pickup_deadline__gt=timezone.now()
    ).order_by('-created_at')[:6]
    
    # Statistics for home page
    total_donations = Donation.objects.count()
    total_organizations = HelpSeeker.objects.filter(verification_status='verified').count()
    total_food_saved = Donation.objects.filter(category__name='Food').count() * 5
    active_donors = DonorProfile.objects.count()
    
    context = {
        'categories': categories,
        'help_seeker_types': help_seeker_types,
        'recent_donations': recent_donations,
        'total_donations': total_donations,
        'total_organizations': total_organizations,
        'total_food_saved': total_food_saved,
        'active_donors': active_donors,
    }
    return render(request, 'donations/home.html', context)


def donation_list(request):
    """Display all available donations with filtering"""
    donations = Donation.objects.filter(
        status='available',
        pickup_deadline__gt=timezone.now()
    ).order_by('-created_at')
    
    # Filter by category if provided
    category_id = request.GET.get('category')
    if category_id:
        donations = donations.filter(category_id=category_id)
    
    context = {
        'donations': donations,
        'categories': DonationCategory.objects.all(),
    }
    return render(request, 'donations/donation_list.html', context)


@login_required
def donation_detail(request, pk):
    """View donation details and handle requests"""
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation_request = form.save(commit=False)
            donation_request.donation = donation
            donation_request.requester = request.user
            donation_request.save()
            
            # Create notification for donor
            Notification.objects.create(
                user=donation.donor.user,
                message=f"{request.user.username} has requested your donation: {donation.title}",
                link=f"/donations/{donation.id}/"
            )
            
            messages.success(request, 'Donation request sent successfully!')
            return redirect('donation_detail', pk=pk)
    else:
        form = DonationRequestForm()
    
    context = {
        'donation': donation,
        'form': form,
    }
    return render(request, 'donations/donation_detail.html', context)


@login_required
def my_donations(request):
    """Display user's donation history"""
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    donations = Donation.objects.filter(donor=donor_profile).order_by('-created_at')
    return render(request, 'donations/my_donations.html', {'donations': donations})


@login_required
def donation_requests(request, donation_id):
    """View requests for a specific donation"""
    donation = get_object_or_404(Donation, id=donation_id, donor__user=request.user)
    requests = DonationRequest.objects.filter(donation=donation)
    
    return render(request, 'donations/donation_requests.html', {
        'donation': donation,
        'requests': requests
    })


@login_required
def update_request_status(request, request_id, status):
    """Update status of a donation request"""
    donation_request = get_object_or_404(DonationRequest, id=request_id)
    
    # Authorization check
    if donation_request.donation.donor.user != request.user:
        messages.error(request, 'You are not authorized to perform this action.')
        return redirect('home')
    
    donation_request.status = status
    donation_request.save()
    
    if status == 'accepted':
        donation_request.donation.status = 'reserved'
        donation_request.donation.save()
    
    # Notify requester
    Notification.objects.create(
        user=donation_request.requester,
        message=f"Your donation request for {donation_request.donation.title} has been {status}",
        link=f"/donations/{donation_request.donation.id}/"
    )
    
    messages.success(request, f'Request {status} successfully!')
    return redirect('donation_requests', donation_id=donation_request.donation.id)


@login_required
def create_donation(request):
    """Create a new donation"""
    # Get or create donor profile
    donor_profile, created = DonorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'organization_name': request.user.username,
            'user_type': 'individual',
            'phone': getattr(request.user.userprofile, 'phone', 'Not provided'),
            'address': getattr(request.user.userprofile, 'address', 'Not provided'),
            'city': getattr(request.user.userprofile, 'city', 'Not provided'),
            'state': getattr(request.user.userprofile, 'state', 'Not provided'),
            'pincode': getattr(request.user.userprofile, 'pincode', '000000'),
        }
    )
    
    if created:
        messages.info(request, 'A donor profile has been automatically created for you.')

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = donor_profile
            donation.save()
            form.save_m2m()  # Save many-to-many fields
            messages.success(request, 'Donation created successfully!')
            return redirect('donation_list')
    else:
        form = DonationForm()
    
    return render(request, 'donations/create_donation.html', {'form': form})


@login_required
def setup_donor_profile(request):
    """Initial donor profile setup"""
    try:
        donor_profile = DonorProfile.objects.get(user=request.user)
        return redirect('update_donor_profile')
    except DonorProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES)
        if form.is_valid():
            donor_profile = form.save(commit=False)
            donor_profile.user = request.user
            donor_profile.save()
            messages.success(request, 'Donor profile created successfully!')
            return redirect('create_donation')
    else:
        # Pre-fill with user profile data if available
        try:
            user_profile = request.user.userprofile
            initial_data = {
                'phone': user_profile.phone,
                'address': user_profile.address,
                'city': user_profile.city,
                'state': user_profile.state,
                'pincode': user_profile.pincode,
            }
            form = DonorProfileForm(initial=initial_data)
        except:
            form = DonorProfileForm()
    
    return render(request, 'donations/setup_donor_profile.html', {'form': form})


@login_required
def update_donor_profile(request):
    """Update existing donor profile"""
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donor profile updated successfully!')
            return redirect('profile')
    else:
        form = DonorProfileForm(instance=donor_profile)
    
    return render(request, 'donations/update_donor_profile.html', {'form': form})


@login_required
def register_help_seeker(request):
    """Register as a help seeker organization"""
    try:
        help_seeker = HelpSeeker.objects.get(user=request.user)
        messages.info(request, 'You already have a help seeker profile.')
        return redirect('help_seeker_dashboard')
    except HelpSeeker.DoesNotExist:
        pass

    if request.method == 'POST':
        form = HelpSeekerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            help_seeker = form.save(commit=False)
            help_seeker.user = request.user
            help_seeker.save()
            messages.success(request, 'Help seeker profile created successfully! Awaiting verification.')
            return redirect('help_seeker_dashboard')
    else:
        form = HelpSeekerRegistrationForm()
    
    context = {
        'form': form,
        'seeker_types': HelpSeekerType.objects.all(),
    }
    return render(request, 'donations/register_help_seeker.html', context)


@login_required
def help_seeker_dashboard(request):
    """Dashboard for help seeker organizations"""
    try:
        help_seeker = HelpSeeker.objects.get(user=request.user)
    except HelpSeeker.DoesNotExist:
        messages.warning(request, 'Please register as a help seeker first.')
        return redirect('register_help_seeker')
    
    help_requests = HelpRequest.objects.filter(help_seeker=help_seeker)
    donation_matches = DonationMatch.objects.filter(help_seeker=help_seeker)
    
    context = {
        'help_seeker': help_seeker,
        'help_requests': help_requests,
        'donation_matches': donation_matches,
    }
    return render(request, 'donations/help_seeker_dashboard.html', context)


@login_required
def create_help_request(request):
    """Create a help request for organizations"""
    try:
        help_seeker = HelpSeeker.objects.get(user=request.user)
    except HelpSeeker.DoesNotExist:
        messages.warning(request, 'Please register as a help seeker first.')
        return redirect('register_help_seeker')
    
    if request.method == 'POST':
        form = HelpRequestForm(request.POST)
        if form.is_valid():
            help_request = form.save(commit=False)
            help_request.help_seeker = help_seeker
            help_request.save()
            messages.success(request, 'Help request created successfully!')
            return redirect('help_seeker_dashboard')
    else:
        form = HelpRequestForm()
    
    context = {
        'form': form,
        'categories': DonationCategory.objects.all(),
    }
    return render(request, 'donations/create_help_request.html', context)


@login_required
def nearby_help_seekers(request, donation_id):
    """Find nearby help seekers for a donation"""
    donation = get_object_or_404(Donation, id=donation_id, donor__user=request.user)
    
    if not donation.latitude or not donation.longitude:
        messages.warning(request, 'Please update your donation with a valid address for location-based matching.')
        return redirect('donation_detail', pk=donation_id)
    
    # Get verified help seekers within 50km radius
    help_seekers = HelpSeeker.objects.filter(
        verification_status='verified',
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    nearby_seekers = []
    for seeker in help_seekers:
        distance = seeker.calculate_distance(donation.latitude, donation.longitude)
        if distance and distance <= 50:  # Within 50km
            # Calculate match score based on distance and preferences
            match_score = max(0, 100 - (distance * 2))  # Distance factor
            if donation.preferred_help_seekers.filter(id=seeker.seeker_type.id).exists():
                match_score += 20  # Preference bonus
            
            nearby_seekers.append({
                'seeker': seeker,
                'distance': round(distance, 2),
                'match_score': min(100, match_score)
            })
    
    # Sort by match score (highest first)
    nearby_seekers.sort(key=lambda x: x['match_score'], reverse=True)
    
    context = {
        'donation': donation,
        'nearby_seekers': nearby_seekers,
    }
    return render(request, 'donations/nearby_help_seekers.html', context)


@login_required
def create_donation_match(request, donation_id, seeker_id):
    """Create a donation match proposal"""
    donation = get_object_or_404(Donation, id=donation_id, donor__user=request.user)
    help_seeker = get_object_or_404(HelpSeeker, id=seeker_id, verification_status='verified')
    
    # Calculate distance and match score
    distance = help_seeker.calculate_distance(donation.latitude, donation.longitude)
    match_score = max(0, 100 - (distance * 2)) if distance else 50
    
    if request.method == 'POST':
        form = DonationMatchForm(request.POST)
        if form.is_valid():
            donation_match = form.save(commit=False)
            donation_match.donation = donation
            donation_match.help_seeker = help_seeker
            donation_match.distance_km = distance
            donation_match.match_score = match_score
            donation_match.save()
            
            # Create notification for help seeker
            Notification.objects.create(
                user=help_seeker.user,
                message=f"{request.user.username} wants to donate '{donation.title}' to your organization",
                link=f"/donation-matches/{donation_match.id}/"
            )
            
            messages.success(request, 'Donation match proposal sent successfully!')
            return redirect('my_donations')
    else:
        form = DonationMatchForm()
    
    context = {
        'donation': donation,
        'help_seeker': help_seeker,
        'distance': distance,
        'match_score': match_score,
        'form': form,
    }
    return render(request, 'donations/create_donation_match.html', context)


@login_required
def donation_match_detail(request, match_id):
    """View and manage donation match details"""
    donation_match = get_object_or_404(DonationMatch, id=match_id)
    
    # Check if user has permission to view this match
    if request.user not in [donation_match.donation.donor.user, donation_match.help_seeker.user]:
        messages.error(request, 'You are not authorized to view this match.')
        return redirect('home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept' and request.user == donation_match.help_seeker.user:
            donation_match.status = 'accepted'
            donation_match.seeker_response = request.POST.get('response_message', '')
            donation_match.save()
            
            # Notify donor
            Notification.objects.create(
                user=donation_match.donation.donor.user,
                message=f"{donation_match.help_seeker.organization_name} has accepted your donation offer",
                link=f"/donation-matches/{donation_match.id}/"
            )
            messages.success(request, 'Donation match accepted!')
            
        elif action == 'reject' and request.user == donation_match.help_seeker.user:
            donation_match.status = 'rejected'
            donation_match.seeker_response = request.POST.get('response_message', '')
            donation_match.save()
            messages.info(request, 'Donation match rejected.')
        
        elif action == 'delivered' and request.user == donation_match.donation.donor.user:
            donation_match.status = 'delivered'
            donation_match.actual_delivery = timezone.now()
            donation_match.save()
            messages.success(request, 'Donation marked as delivered!')
    
    context = {
        'donation_match': donation_match,
    }
    return render(request, 'donations/donation_match_detail.html', context)


@login_required
def help_seeker_directory(request):
    """Browse all verified help seekers"""
    help_seekers = HelpSeeker.objects.filter(verification_status='verified')
    
    # Filter by type if provided
    seeker_type = request.GET.get('type')
    if seeker_type:
        help_seekers = help_seekers.filter(seeker_type_id=seeker_type)
    
    # Filter by city if provided
    city = request.GET.get('city')
    if city:
        help_seekers = help_seekers.filter(city__icontains=city)
    
    context = {
        'help_seekers': help_seekers,
        'seeker_types': HelpSeekerType.objects.all(),
    }
    return render(request, 'donations/help_seeker_directory.html', context)


def public_help_seekers_map(request):
    """Public map view of help seekers"""
    help_seekers = HelpSeeker.objects.filter(
        verification_status='verified',
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    seeker_data = []
    for seeker in help_seekers:
        seeker_data.append({
            'name': seeker.organization_name,
            'type': seeker.seeker_type.name,
            'lat': seeker.latitude,
            'lng': seeker.longitude,
            'address': f"{seeker.address}, {seeker.city}",
            'phone': seeker.phone,
            'urgent': seeker.is_urgent,
            'url': f"/help-seekers/{seeker.id}/"
        })
    
    context = {
        'help_seekers_json': json.dumps(seeker_data),
        'seeker_types': HelpSeekerType.objects.all(),
    }
    return render(request, 'donations/public_help_seekers_map.html', context)


# Verification Views
@login_required
def submit_donor_verification(request):
    """Submit donor verification documents"""
    try:
        donor_profile = DonorProfile.objects.get(user=request.user)
    except DonorProfile.DoesNotExist:
        messages.error(request, 'Please complete your donor profile first.')
        return redirect('setup_donor_profile')

    if request.method == 'POST':
        form = DonorVerificationForm(request.POST, request.FILES, instance=donor_profile)
        if form.is_valid():
            donor_profile = form.save(commit=False)
            donor_profile.verification_status = 'pending'
            donor_profile.save()
            
            # Create verification request
            VerificationRequest.objects.create(
                user=request.user,
                verification_type='donor',
                document=donor_profile.verification_document,
                status='pending'
            )
            
            messages.success(request, 'Verification request submitted successfully! We will review your documents soon.')
            return redirect('profile')
    else:
        form = DonorVerificationForm(instance=donor_profile)
    
    context = {'form': form}
    return render(request, 'donations/submit_verification.html', context)


@login_required
def submit_help_seeker_verification(request):
    """Submit help seeker verification documents"""
    try:
        help_seeker = HelpSeeker.objects.get(user=request.user)
    except HelpSeeker.DoesNotExist:
        messages.error(request, 'Please register as a help seeker first.')
        return redirect('register_help_seeker')

    if request.method == 'POST':
        form = HelpSeekerVerificationForm(request.POST, request.FILES, instance=help_seeker)
        if form.is_valid():
            help_seeker = form.save(commit=False)
            help_seeker.verification_status = 'pending'
            help_seeker.save()
            
            # Create verification request
            VerificationRequest.objects.create(
                user=request.user,
                verification_type='help_seeker',
                document=help_seeker.verification_document,
                status='pending'
            )
            
            messages.success(request, 'Verification request submitted successfully! We will review your documents soon.')
            return redirect('help_seeker_dashboard')
    else:
        form = HelpSeekerVerificationForm(instance=help_seeker)
    
    context = {'form': form}
    return render(request, 'donations/submit_verification.html', context)


@staff_member_required
def admin_verification_dashboard(request):
    """Admin dashboard for verification requests"""
    verification_requests = VerificationRequest.objects.filter(
        status__in=['pending', 'under_review']
    ).order_by('submitted_at')
    
    context = {
        'verification_requests': verification_requests,
    }
    return render(request, 'donations/admin_verification_dashboard.html', context)


@staff_member_required
def review_verification(request, request_id):
    """Review and process verification requests"""
    verification_request = get_object_or_404(VerificationRequest, id=request_id)
    
    if request.method == 'POST':
        form = AdminVerificationForm(request.POST, instance=verification_request)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.reviewed_by = request.user
            verification.reviewed_at = timezone.now()
            verification.save()
            
            # Update the respective profile based on verification type
            if verification.verification_type == 'donor':
                donor_profile = DonorProfile.objects.get(user=verification.user)
                donor_profile.verification_status = verification.status
                if verification.status == 'approved':
                    donor_profile.verified_by = request.user
                    donor_profile.verified_at = timezone.now()
                donor_profile.save()
                
            elif verification.verification_type == 'help_seeker':
                help_seeker = HelpSeeker.objects.get(user=verification.user)
                help_seeker.verification_status = verification.status
                if verification.status == 'approved':
                    help_seeker.verified_by = request.user
                    help_seeker.verified_at = timezone.now()
                help_seeker.save()
            
            # Create notification for user
            status_message = "approved" if verification.status == 'approved' else "rejected"
            Notification.objects.create(
                user=verification.user,
                message=f"Your {verification.get_verification_type_display()} has been {status_message}. {verification.notes}",
                link="/profile/"
            )
            
            messages.success(request, f'Verification {verification.status}!')
            return redirect('admin_verification_dashboard')
    else:
        form = AdminVerificationForm(instance=verification_request)
    
    # Get the profile being verified
    profile = None
    if verification_request.verification_type == 'donor':
        profile = DonorProfile.objects.get(user=verification_request.user)
    elif verification_request.verification_type == 'help_seeker':
        profile = HelpSeeker.objects.get(user=verification_request.user)
    
    context = {
        'verification_request': verification_request,
        'form': form,
        'profile': profile,
    }
    return render(request, 'donations/review_verification.html', context)


@login_required
def verification_status(request):
    """View verification status for current user"""
    donor_verification = None
    help_seeker_verification = None
    
    try:
        donor_profile = DonorProfile.objects.get(user=request.user)
        donor_verification = VerificationRequest.objects.filter(
            user=request.user, 
            verification_type='donor'
        ).order_by('-submitted_at').first()
    except DonorProfile.DoesNotExist:
        pass
    
    try:
        help_seeker = HelpSeeker.objects.get(user=request.user)
        help_seeker_verification = VerificationRequest.objects.filter(
            user=request.user, 
            verification_type='help_seeker'
        ).order_by('-submitted_at').first()
    except HelpSeeker.DoesNotExist:
        pass
    
    context = {
        'donor_verification': donor_verification,
        'help_seeker_verification': help_seeker_verification,
    }
    return render(request, 'donations/verification_status.html', context)

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import User, DonorProfile, HelpSeeker, VerificationRequest

def superuser_required(view_func):
    """Decorator to ensure only superusers can access the view"""
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/admin/login/'
    )(view_func)
    return decorated_view_func

@superuser_required
def superuser_verification_panel(request):
    """Custom admin panel for superuser to verify and manage profiles"""
    
    # Get filter parameters
    profile_type = request.GET.get('type', 'all')
    verification_status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    # Base querysets
    donor_profiles = DonorProfile.objects.select_related('user').all()
    seeker_profiles = HelpSeeker.objects.select_related('user').all()
    verification_requests = VerificationRequest.objects.select_related('user').all()
    
    # Apply filters
    if search_query:
        donor_profiles = donor_profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(organization_name__icontains=search_query) |
            Q(city__icontains=search_query)
        )
        seeker_profiles = seeker_profiles.filter(
            Q(organization_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if verification_status != 'all':
        donor_profiles = donor_profiles.filter(verification_status=verification_status)
        seeker_profiles = seeker_profiles.filter(verification_status=verification_status)
    
    # Counts for dashboard
    counts = {
        'total_donors': DonorProfile.objects.count(),
        'verified_donors': DonorProfile.objects.filter(verification_status='verified').count(),
        'pending_donors': DonorProfile.objects.filter(verification_status='pending').count(),
        'total_seekers': HelpSeeker.objects.count(),
        'verified_seekers': HelpSeeker.objects.filter(verification_status='verified').count(),
        'pending_seekers': HelpSeeker.objects.filter(verification_status='pending').count(),
        'pending_requests': VerificationRequest.objects.filter(status='pending').count(),
    }
    
    context = {
        'donor_profiles': donor_profiles,
        'seeker_profiles': seeker_profiles,
        'verification_requests': verification_requests,
        'counts': counts,
        'current_filters': {
            'type': profile_type,
            'status': verification_status,
            'q': search_query,
        },
        'verification_status_choices': DonorProfile.VERIFICATION_STATUS,
    }
    
    return render(request, 'donations/admin/superuser_panel.html', context)

@superuser_required
def verify_profile(request, profile_type, profile_id):
    """Verify a specific profile"""
    if request.method == 'POST':
        try:
            if profile_type == 'donor':
                profile = get_object_or_404(DonorProfile, id=profile_id)
                profile.verification_status = 'verified'
                profile.verified_at = timezone.now()
                profile.verified_by = request.user
                profile.save()
                messages.success(request, f'Donor profile for {profile.user.username} verified successfully!')
                
            elif profile_type == 'seeker':
                profile = get_object_or_404(HelpSeeker, id=profile_id)
                profile.verification_status = 'verified'
                profile.verified_at = timezone.now()
                profile.verified_by = request.user
                profile.save()
                messages.success(request, f'Help seeker profile for {profile.organization_name} verified successfully!')
                
        except Exception as e:
            messages.error(request, f'Error verifying profile: {str(e)}')
    
    return redirect('superuser_verification_panel')

@superuser_required
def reject_profile(request, profile_type, profile_id):
    """Reject a specific profile"""
    if request.method == 'POST':
        try:
            if profile_type == 'donor':
                profile = get_object_or_404(DonorProfile, id=profile_id)
                profile.verification_status = 'rejected'
                profile.verified_at = timezone.now()
                profile.verified_by = request.user
                profile.save()
                messages.success(request, f'Donor profile for {profile.user.username} rejected!')
                
            elif profile_type == 'seeker':
                profile = get_object_or_404(HelpSeeker, id=profile_id)
                profile.verification_status = 'rejected'
                profile.verified_at = timezone.now()
                profile.verified_by = request.user
                profile.save()
                messages.success(request, f'Help seeker profile for {profile.organization_name} rejected!')
                
        except Exception as e:
            messages.error(request, f'Error rejecting profile: {str(e)}')
    
    return redirect('superuser_verification_panel')

@superuser_required
def delete_profile(request, profile_type, profile_id):
    """Delete a specific profile and optionally the user"""
    if request.method == 'POST':
        try:
            if profile_type == 'donor':
                profile = get_object_or_404(DonorProfile, id=profile_id)
                username = profile.user.username
                user = profile.user
                profile.delete()
                # Optionally delete user account as well
                if request.POST.get('delete_user') == 'true':
                    user.delete()
                    messages.success(request, f'Donor profile and user account for {username} deleted successfully!')
                else:
                    messages.success(request, f'Donor profile for {username} deleted successfully!')
                    
            elif profile_type == 'seeker':
                profile = get_object_or_404(HelpSeeker, id=profile_id)
                org_name = profile.organization_name
                user = profile.user
                profile.delete()
                # Optionally delete user account as well
                if request.POST.get('delete_user') == 'true':
                    user.delete()
                    messages.success(request, f'Help seeker profile and user account for {org_name} deleted successfully!')
                else:
                    messages.success(request, f'Help seeker profile for {org_name} deleted successfully!')
                    
        except Exception as e:
            messages.error(request, f'Error deleting profile: {str(e)}')
    
    return redirect('superuser_verification_panel')

@superuser_required
def bulk_verify_profiles(request):
    """Bulk verify multiple profiles"""
    if request.method == 'POST':
        donor_ids = request.POST.getlist('donor_ids')
        seeker_ids = request.POST.getlist('seeker_ids')
        
        verified_count = 0
        
        # Verify donors
        for donor_id in donor_ids:
            try:
                donor = DonorProfile.objects.get(id=donor_id)
                donor.verification_status = 'verified'
                donor.verified_at = timezone.now()
                donor.verified_by = request.user
                donor.save()
                verified_count += 1
            except DonorProfile.DoesNotExist:
                pass
        
        # Verify seekers
        for seeker_id in seeker_ids:
            try:
                seeker = HelpSeeker.objects.get(id=seeker_id)
                seeker.verification_status = 'verified'
                seeker.verified_at = timezone.now()
                seeker.verified_by = request.user
                seeker.save()
                verified_count += 1
            except HelpSeeker.DoesNotExist:
                pass
        
        messages.success(request, f'{verified_count} profiles verified successfully!')
    
    return redirect('superuser_verification_panel')

@superuser_required
def bulk_delete_profiles(request):
    """Bulk delete multiple profiles"""
    if request.method == 'POST':
        donor_ids = request.POST.getlist('donor_ids')
        seeker_ids = request.POST.getlist('seeker_ids')
        delete_users = request.POST.get('delete_users') == 'true'
        
        deleted_count = 0
        
        # Delete donors
        for donor_id in donor_ids:
            try:
                donor = DonorProfile.objects.get(id=donor_id)
                user = donor.user
                donor.delete()
                if delete_users:
                    user.delete()
                deleted_count += 1
            except DonorProfile.DoesNotExist:
                pass
        
        # Delete seekers
        for seeker_id in seeker_ids:
            try:
                seeker = HelpSeeker.objects.get(id=seeker_id)
                user = seeker.user
                seeker.delete()
                if delete_users:
                    user.delete()
                deleted_count += 1
            except HelpSeeker.DoesNotExist:
                pass
        
        messages.success(request, f'{deleted_count} profiles deleted successfully!')
    
    return redirect('superuser_verification_panel')