from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class VerificationRequest(models.Model):
    VERIFICATION_TYPES = [
        ('donor', 'Donor Verification'),
        ('help_seeker', 'Help Seeker Verification'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_more_info', 'Needs More Information'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    document = models.FileField(upload_to='verification_docs/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='reviewed_verifications')
    notes = models.TextField(blank=True, help_text="Admin notes or reason for rejection")
    
    class Meta:
        verbose_name = "Verification Request"
        verbose_name_plural = "Verification Requests"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_verification_type_display()}"


class DonorProfile(models.Model):
    USER_TYPES = [
        ('individual', 'Individual'),
        ('hotel', 'Hotel/Restaurant'),
        ('catering', 'Catering Service'),
        ('banquet', 'Banquet Hall'),
        ('hostel', 'Hostel/Mess'),
        ('corporate', 'Corporate Office'),
        ('other', 'Other Organization'),
    ]
    
    VERIFICATION_STATUS = [
        ('not_submitted', 'Not Submitted'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='not_submitted')
    verification_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='verified_donors')
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Donor Profile"
        verbose_name_plural = "Donor Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

    @property
    def is_verified(self):
        return self.verification_status == 'verified'
    
    @property
    def display_name(self):
        return self.organization_name or self.user.username


class DonationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-box')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donation Category"
        verbose_name_plural = "Donation Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class HelpSeekerType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Help Seeker Type"
        verbose_name_plural = "Help Seeker Types"
        ordering = ['name']

    def __str__(self):
        return self.name


class HelpSeeker(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization_name = models.CharField(max_length=255)
    seeker_type = models.ForeignKey(HelpSeekerType, on_delete=models.CASCADE)
    description = models.TextField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    capacity = models.PositiveIntegerField(help_text="Number of people served", null=True, blank=True)
    verification_document = models.FileField(upload_to='seeker_verification/', blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    is_urgent = models.BooleanField(default=False)
    urgent_needs = models.TextField(blank=True, help_text="Current urgent needs")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='verified_seekers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Help Seeker"
        verbose_name_plural = "Help Seekers"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Geocode address to get coordinates
        if self.address and not (self.latitude and self.longitude):
            self._geocode_address()
        super().save(*args, **kwargs)

    def _geocode_address(self):
        """Helper method to geocode address"""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="uhv_donation")
            location = geolocator.geocode(f"{self.address}, {self.city}, {self.state}, {self.pincode}")
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        except Exception as e:
            print(f"Geocoding error: {e}")

    def calculate_distance(self, donor_lat, donor_lng):
        """Calculate distance between help seeker and donor location"""
        if self.latitude and self.longitude and donor_lat and donor_lng:
            try:
                import geopy.distance
                coords_1 = (self.latitude, self.longitude)
                coords_2 = (donor_lat, donor_lng)
                return geopy.distance.distance(coords_1, coords_2).km
            except ImportError:
                return self._calculate_simple_distance(donor_lat, donor_lng)
        return None

    def _calculate_simple_distance(self, donor_city, donor_state):
        """Fallback distance calculation based on city/state matching"""
        if self.city.lower() == donor_city.lower() and self.state.lower() == donor_state.lower():
            return 0  # Same location
        elif self.city.lower() == donor_city.lower():
            return 5  # Same city
        elif self.state.lower() == donor_state.lower():
            return 20  # Same state
        else:
            return 50  # Different state

    @property
    def is_verified(self):
        return self.verification_status == 'verified'

    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"

    def __str__(self):
        return f"{self.organization_name} - {self.seeker_type.name}"


class Donation(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('collected', 'Collected'),
        ('expired', 'Expired'),
    ]
    
    FOOD_TYPE_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non_veg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
        ('eggetarian', 'Eggetarian'),
    ]
    
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='donations')
    category = models.ForeignKey(DonationCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    
    # Food specific fields
    food_type = models.CharField(max_length=15, choices=FOOD_TYPE_CHOICES, blank=True, null=True)
    cooked_time = models.DateTimeField(blank=True, null=True)
    best_before = models.DateTimeField(blank=True, null=True)
    
    # General fields
    pickup_address = models.TextField()
    pickup_city = models.CharField(max_length=100, blank=True)
    pickup_state = models.CharField(max_length=100, blank=True)
    pickup_deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Location fields
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Preferred organizations
    preferred_help_seekers = models.ManyToManyField(HelpSeekerType, blank=True, 
                                                   help_text="Preferred types of organizations for this donation")
    
    # Image fields
    image = models.ImageField(upload_to='donation_images/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'pickup_deadline']),
            models.Index(fields=['category', 'status']),
        ]

    def is_expired(self):
        return timezone.now() > self.pickup_deadline
    
    def time_until_expiry(self):
        """Returns timedelta until expiry"""
        return self.pickup_deadline - timezone.now()
    
    @property
    def is_available(self):
        return self.status == 'available' and not self.is_expired()
    
    @property
    def donor_name(self):
        return self.donor.display_name

    def save(self, *args, **kwargs):
        # Auto-expire donations
        if self.is_expired() and self.status == 'available':
            self.status = 'expired'
        
        # Extract city and state from pickup address if not provided
        self._extract_location_from_address()
        
        # Geocode address to get coordinates if not already set
        if self.pickup_address and not (self.latitude and self.longitude):
            self._geocode_address()
        
        super().save(*args, **kwargs)

    def _extract_location_from_address(self):
        """Extract city and state from pickup address"""
        if self.pickup_address and (not self.pickup_city or not self.pickup_state):
            try:
                address_parts = [part.strip() for part in self.pickup_address.split(',')]
                if len(address_parts) >= 2:
                    self.pickup_city = address_parts[-2]
                    self.pickup_state = address_parts[-1]
            except Exception:
                pass

    def _geocode_address(self):
        """Geocode pickup address to get coordinates"""
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="uhv_donation")
            location = geolocator.geocode(self.pickup_address)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        except Exception as e:
            print(f"Geocoding error for donation: {e}")

    def __str__(self):
        return f"{self.title} ({self.quantity})"


class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    requested_quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donation Request"
        verbose_name_plural = "Donation Requests"
        ordering = ['-created_at']
        unique_together = ['donation', 'requester']

    def __str__(self):
        return f"Request for {self.donation.title} by {self.requester.username}"

    # Remove the save method that was causing issues, or keep it without email sending
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Don't send emails from here - let views handle it
        # Email sending is now handled in views.py


class DonationMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
    ]
    
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='matches')
    help_seeker = models.ForeignKey(HelpSeeker, on_delete=models.CASCADE, related_name='matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    distance_km = models.FloatField(null=True, blank=True)
    match_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    donor_message = models.TextField(blank=True)
    seeker_response = models.TextField(blank=True)
    scheduled_pickup = models.DateTimeField(null=True, blank=True)
    actual_delivery = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Donation Match"
        verbose_name_plural = "Donation Matches"
        ordering = ['-created_at']

    @property
    def is_active(self):
        return self.status in ['pending', 'accepted']

    def __str__(self):
        return f"{self.donation.title} → {self.help_seeker.organization_name}"


class HelpRequest(models.Model):
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    help_seeker = models.ForeignKey(HelpSeeker, on_delete=models.CASCADE, related_name='help_requests')
    category = models.ForeignKey(DonationCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    quantity_needed = models.PositiveIntegerField()
    urgency = models.CharField(max_length=20, choices=URGENCY_LEVELS, default='medium')
    is_active = models.BooleanField(default=True)
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Help Request"
        verbose_name_plural = "Help Requests"
        ordering = ['-urgency', '-created_at']

    @property
    def is_urgent(self):
        return self.urgency in ['high', 'critical']

    def __str__(self):
        return f"{self.title} - {self.help_seeker.organization_name}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def mark_as_read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ['-created_at']
        unique_together = ['user', 'donation']

    @property
    def rating_stars(self):
        return '⭐' * self.rating

    def __str__(self):
        return f"Feedback by {self.user.username} for {self.donation.title}"


class Rating(models.Model):
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='given_ratings')
    help_seeker = models.ForeignKey(HelpSeeker, on_delete=models.CASCADE, related_name='received_ratings')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"
        ordering = ['-created_at']
        unique_together = ['donor', 'help_seeker']

    @property
    def average_rating(self):
        """Calculate average rating for a help seeker"""
        ratings = Rating.objects.filter(help_seeker=self.help_seeker)
        if ratings.exists():
            return ratings.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    def __str__(self):
        return f"Rating {self.rating} for {self.help_seeker.organization_name}"

# Remove or comment out the problematic signal
# @receiver(post_save, sender=DonationRequest)
# def send_donation_request_notification(sender, instance, created, **kwargs):
#     if created:
#         instance.send_notification_emails()  # This causes the error