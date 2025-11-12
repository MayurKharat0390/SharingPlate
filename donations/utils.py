from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

def send_donation_request_email(donation_request):
    """
    Send email notification to donor when someone requests their donation
    """
    try:
        donation = donation_request.donation
        donor = donation.donor.user
        requester = donation_request.requester
        
        # Get requester profile (could be donor or help seeker)
        requester_profile = None
        if hasattr(requester, 'donorprofile'):
            requester_profile = requester.donorprofile
        elif hasattr(requester, 'helpseeker'):
            requester_profile = requester.helpseeker
        
        # Email context
        context = {
            'donation': donation,
            'donation_request': donation_request,
            'requester': requester,
            'requester_profile': requester_profile,
            'donor': donor,
            'admin_url': settings.SITE_URL + reverse('admin:donations_donationrequest_change', args=[donation_request.id]),
            'site_url': settings.SITE_URL,
        }
        
        # Subject line
        subject = f"New Donation Request: {donation.title}"
        
        # Render HTML content
        html_content = render_to_string('emails/donation_request_notification.html', context)
        
        # Render plain text content
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[donor.email],  # Send to donor's email
            reply_to=[settings.DEFAULT_FROM_EMAIL],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        return True
        
    except Exception as e:
        print(f"Error sending donation request email: {str(e)}")
        return False

def send_admin_notification_email(donation_request):
    """
    Send notification to admin as well (optional)
    """
    try:
        donation = donation_request.donation
        requester = donation_request.requester
        
        subject = f"📦 New Donation Request - {donation.title}"
        
        message = f"""
        New donation request received:
        
        Donation: {donation.title}
        Donor: {donation.donor.user.username} ({donation.donor.user.email})
        Requester: {requester.username} ({requester.email})
        Requested Quantity: {donation_request.requested_quantity}
        Requested At: {donation_request.created_at}
        
        Manage: {settings.SITE_URL}/admin/donations/donationrequest/{donation_request.id}/change/
        """
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.ADMIN_EMAIL],
        )
        
        email.send(fail_silently=True)
        return True
        
    except Exception as e:
        print(f"Error sending admin notification: {str(e)}")
        return False