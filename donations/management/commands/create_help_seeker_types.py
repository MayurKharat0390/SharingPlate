from django.core.management.base import BaseCommand
from donations.models import HelpSeekerType

class Command(BaseCommand):
    help = 'Create initial help seeker types'

    def handle(self, *args, **options):
        types_data = [
            {
                'name': 'Old Age Home',
                'description': 'Senior citizen care facilities providing shelter and care for elderly people',
                'icon': 'fas fa-wheelchair'
            },
            {
                'name': 'Orphanage',
                'description': 'Children\'s homes providing care and shelter for orphaned and vulnerable children',
                'icon': 'fas fa-child'
            },
            {
                'name': 'Homeless Shelter',
                'description': 'Temporary accommodation and support services for homeless individuals and families',
                'icon': 'fas fa-home'
            },
            {
                'name': 'Food Bank',
                'description': 'Organizations that collect and distribute food to those in need',
                'icon': 'fas fa-utensils'
            },
            {
                'name': 'Disability Center',
                'description': 'Facilities providing support and services for people with disabilities',
                'icon': 'fas fa-universal-access'
            },
            {
                'name': 'Women\'s Shelter',
                'description': 'Safe spaces and support services for women in crisis situations',
                'icon': 'fas fa-female'
            },
            {
                'name': 'Community Center',
                'description': 'Local centers serving various community needs and vulnerable groups',
                'icon': 'fas fa-users'
            },
        ]

        for type_data in types_data:
            obj, created = HelpSeekerType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created: {obj.name}')
                )