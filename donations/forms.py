from django import forms
from .models import (
    Donation, DonorProfile, DonationRequest, HelpSeeker, 
    HelpRequest, DonationMatch, VerificationRequest, DonationCategory
)


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = [
            'organization_name', 'user_type', 'phone', 'address', 
            'city', 'state', 'pincode', 'verification_document'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your complete address'}),
        }
        help_texts = {
            'organization_name': 'Leave blank if you are an individual donor',
            'verification_document': 'Upload ID proof or organization registration document for verification',
        }


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            'category', 'title', 'description', 'quantity', 'food_type', 
            'cooked_time', 'best_before', 'pickup_address', 'pickup_deadline', 
            'image', 'preferred_help_seekers'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Describe your donation item in detail...'
            }),
            'pickup_address': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Where can the recipient pickup the donation?'
            }),
            'cooked_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'best_before': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'pickup_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'preferred_help_seekers': forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            'pickup_deadline': 'Set the deadline by when the donation must be picked up',
            'preferred_help_seekers': 'Select the types of organizations you prefer to donate to',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the Food category ID for JavaScript
        food_category_id = None
        try:
            food_category = DonationCategory.objects.filter(name='Food').first()
            if food_category:
                food_category_id = food_category.id
        except:
            pass
        
        # Add data attribute for food category ID
        if food_category_id:
            self.fields['category'].widget.attrs.update({
                'data-food-category-id': food_category_id
            })


class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['message', 'requested_quantity']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Tell the donor why you need this donation...'
            }),
        }
        help_texts = {
            'requested_quantity': 'How many items do you need?',
        }


class HelpSeekerRegistrationForm(forms.ModelForm):
    class Meta:
        model = HelpSeeker
        fields = [
            'organization_name', 'seeker_type', 'description', 'phone', 
            'address', 'city', 'state', 'pincode', 'capacity', 
            'verification_document', 'is_urgent', 'urgent_needs'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Describe your organization and its mission...'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Enter your organization\'s complete address'
            }),
            'urgent_needs': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'List your current urgent needs and requirements...'
            }),
        }
        help_texts = {
            'capacity': 'Approximate number of people your organization serves',
            'verification_document': 'Upload organization registration certificate or proof',
            'is_urgent': 'Check if your organization has urgent needs right now',
        }


class HelpRequestForm(forms.ModelForm):
    class Meta:
        model = HelpRequest
        fields = ['category', 'title', 'description', 'quantity_needed', 'urgency', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Need Rice and Lentils for 50 people'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Describe what you need and how it will help your organization...'
            }),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        help_texts = {
            'urgency': 'How urgently do you need these items?',
            'deadline': 'When do you need these items by?',
        }


class DonationMatchForm(forms.ModelForm):
    class Meta:
        model = DonationMatch
        fields = ['donor_message', 'scheduled_pickup']
        widgets = {
            'donor_message': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Add a message for the organization...'
            }),
            'scheduled_pickup': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        help_texts = {
            'scheduled_pickup': 'Propose a date and time for pickup/delivery',
        }


class DonorVerificationForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['verification_document']
        labels = {
            'verification_document': 'Upload Verification Document',
        }
        help_texts = {
            'verification_document': '''
            Accepted documents:
            • Individuals: Aadhar Card, PAN Card, Driver's License, Passport
            • Organizations: Registration Certificate, Business License, GST Certificate
            • Hotels/Restaurants: FSSAI License, Trade License
            ''',
        }


class HelpSeekerVerificationForm(forms.ModelForm):
    class Meta:
        model = HelpSeeker
        fields = ['verification_document']
        labels = {
            'verification_document': 'Upload Organization Verification Document',
        }
        help_texts = {
            'verification_document': '''
            Accepted documents:
            • Registration Certificate
            • Society/Trust Registration
            • License from Government Authority
            • Any official document proving organization legitimacy
            ''',
        }


class AdminVerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Add notes for the user (reason for approval/rejection, additional requirements...)'
            }),
        }
        labels = {
            'status': 'Verification Status',
            'notes': 'Admin Notes',
        }