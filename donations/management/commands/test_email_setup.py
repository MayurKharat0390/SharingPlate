from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from donations.models import Donation, DonationRequest
from donations.email_utils import send_donation_request_email, send_request_status_email

class Command(BaseCommand):
    help = 'Test the email notification system'

    def handle(self, *args, **options):
        # Create a test donation request and send email
        try:
            donor = User.objects.get(username='admin')
            requester = User.objects.filter(is_staff=False).first()
            donation = Donation.objects.filter(donor__user=donor).first()
            
            if donation and requester:
                # Create test donation request
                donation_request = DonationRequest.objects.create(
                    donation=donation,
                    requester=requester,
                    requested_quantity=2,
                    message='This is a test request for email testing'
                )
                
                # Test donation request email
                self.stdout.write('Sending donation request email...')
                send_donation_request_email(donation_request)
                
                # Test status update email
                self.stdout.write('Sending status update email...')
                send_request_status_email(donation_request, 'pending', 'accepted')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Email system test completed successfully!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Need donor, requester, and donation for testing')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing email system: {str(e)}')
            )