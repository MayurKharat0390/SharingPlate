from django.core.management.base import BaseCommand
from donations.models import DonationCategory

class Command(BaseCommand):
    help = 'Create initial donation categories'

    def handle(self, *args, **options):
        categories = [
            {'name': 'Food', 'description': 'Cooked meals, packaged food, fruits and vegetables', 'icon': 'fas fa-utensils'},
            {'name': 'Clothes', 'description': 'New or gently used clothing items', 'icon': 'fas fa-tshirt'},
            {'name': 'Books', 'description': 'Educational books, novels, textbooks', 'icon': 'fas fa-book'},
            {'name': 'Money', 'description': 'Financial donations for various causes', 'icon': 'fas fa-money-bill-wave'},
            {'name': 'Furniture', 'description': 'Household furniture in good condition', 'icon': 'fas fa-couch'},
            {'name': 'Electronics', 'description': 'Working electronic devices', 'icon': 'fas fa-laptop'},
            {'name': 'Medical', 'description': 'Medical supplies and equipment', 'icon': 'fas fa-briefcase-medical'},
            {'name': 'Other', 'description': 'Other types of donations', 'icon': 'fas fa-box'},
        ]

        for category_data in categories:
            category, created = DonationCategory.objects.get_or_create(
                name=category_data['name'],
                defaults=category_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created category: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully created all initial categories!')
        )