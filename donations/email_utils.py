from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

def send_donation_request_email(donation_request):
    """
    Send email to donor when someone requests their donation
    """
    try:
        donation = donation_request.donation
        donor = donation.donor.user
        requester = donation_request.requester
        
        # Get requester profile information
        requester_profile = None
        requester_type = "Individual"
        
        if hasattr(requester, 'donorprofile'):
            requester_profile = requester.donorprofile
            requester_type = requester_profile.get_user_type_display()
        elif hasattr(requester, 'helpseeker'):
            requester_profile = requester.helpseeker
            requester_type = f"Organization ({requester_profile.seeker_type.name})"
        
        # Email context
        context = {
            'donation': donation,
            'donation_request': donation_request,
            'requester': requester,
            'requester_profile': requester_profile,
            'requester_type': requester_type,
            'donor': donor,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
        }
        
        # Subject line
        subject = f"🎁 New Donation Request: {donation.title}"
        
        # Render HTML content
        html_content = render_to_string('emails/donation_request_notification.html', context)
        
        # Render plain text content
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_CONFIG['NOTIFICATIONS'],
            to=[donor.email],
            reply_to=[settings.EMAIL_CONFIG['NOTIFICATIONS']],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        print(f"✅ Donation request email sent to {donor.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending donation request email: {str(e)}")
        return False

def send_request_status_email(donation_request, old_status, new_status):
    """
    Send email to requester when donation request status changes
    """
    try:
        requester = donation_request.requester
        donation = donation_request.donation
        donor = donation.donor.user
        
        # Email context
        context = {
            'donation': donation,
            'donation_request': donation_request,
            'requester': requester,
            'donor': donor,
            'old_status': old_status,
            'new_status': new_status,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
        }
        
        # Subject based on status
        if new_status == 'accepted':
            subject = f"✅ Donation Request Accepted: {donation.title}"
        elif new_status == 'rejected':
            subject = f"❌ Donation Request Declined: {donation.title}"
        elif new_status == 'completed':
            subject = f"🎉 Donation Completed: {donation.title}"
        else:
            subject = f"📝 Donation Request Updated: {donation.title}"
        
        # Render HTML content
        html_content = render_to_string('emails/request_status_update.html', context)
        
        # Render plain text content
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_CONFIG['NOTIFICATIONS'],
            to=[requester.email],
            reply_to=[settings.EMAIL_CONFIG['NOTIFICATIONS']],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        print(f"✅ Request status email sent to {requester.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending request status email: {str(e)}")
        return False

def send_donation_match_email(donation_match, email_type):
    """
    Send emails related to donation matches
    """
    try:
        if email_type == 'proposal':
            # Email to help seeker about new donation offer
            help_seeker = donation_match.help_seeker
            donation = donation_match.donation
            
            context = {
                'donation_match': donation_match,
                'help_seeker': help_seeker,
                'donation': donation,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
                'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
            }
            
            subject = f"🎁 New Donation Offer: {donation.title}"
            html_content = render_to_string('emails/donation_match_proposal.html', context)
            
        elif email_type == 'accepted':
            # Email to donor about accepted offer
            donor = donation_match.donation.donor.user
            help_seeker = donation_match.help_seeker
            
            context = {
                'donation_match': donation_match,
                'donor': donor,
                'help_seeker': help_seeker,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
                'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
            }
            
            subject = f"✅ Donation Accepted: {donation_match.donation.title}"
            html_content = render_to_string('emails/donation_match_accepted.html', context)
            
        elif email_type == 'rejected':
            # Email to donor about rejected offer
            donor = donation_match.donation.donor.user
            help_seeker = donation_match.help_seeker
            
            context = {
                'donation_match': donation_match,
                'donor': donor,
                'help_seeker': help_seeker,
                'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
                'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
            }
            
            subject = f"❌ Donation Declined: {donation_match.donation.title}"
            html_content = render_to_string('emails/donation_match_rejected.html', context)
        
        text_content = strip_tags(html_content)
        
        # Determine recipient
        if email_type == 'proposal':
            recipient = help_seeker.user.email
        else:
            recipient = donor.email
        
        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_CONFIG['NOTIFICATIONS'],
            to=[recipient],
            reply_to=[settings.EMAIL_CONFIG['NOTIFICATIONS']],
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        print(f"✅ Donation match email sent to {recipient}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending donation match email: {str(e)}")
        return False

def send_welcome_email(user):
    """
    Send welcome email to new users
    """
    try:
        context = {
            'user': user,
            'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
            'site_name': getattr(settings, 'SITE_NAME', 'UHV ShareHub'),
        }
        
        subject = f"🎉 Welcome to {getattr(settings, 'SITE_NAME', 'UHV ShareHub')}!"
        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.EMAIL_CONFIG['NOTIFICATIONS'],
            to=[user.email],
            reply_to=[settings.EMAIL_CONFIG['SUPPORT']],
        )
        
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
        
        print(f"✅ Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending welcome email: {str(e)}")
        return False