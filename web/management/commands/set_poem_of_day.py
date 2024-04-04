from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date
from datetime import timedelta
from web.models import PoemOfTheDay, Poem

class Command(BaseCommand):
    help = 'Create PoemOfTheDay instances for a range of dates'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', type=str, help='Start date (YYYY-MM-DD)')
        parser.add_argument('--to', dest='to_date', type=str, help='End date (YYYY-MM-DD)')

    def handle(self, *args, **options):
        from_date = options['from_date']
        to_date = options['to_date']
        
        # Validate and parse the date strings
        try:
            from_date = parse_date(from_date)
            to_date = parse_date(to_date)
            if not from_date or not to_date:
                raise ValueError
        except ValueError:
            raise CommandError('Invalid date format. Use YYYY-MM-DD.')

        # Ensure the from_date is before the to_date
        if from_date > to_date:
            raise CommandError('"From" date must be before "to" date.')

        # Fetch the poem instance
        try:
            poem = Poem.objects.get(id=50600001)
        except Poem.DoesNotExist:
            raise CommandError('Poem with ID 50600001 does not exist.')

        # Create PoemOfTheDay instances
        current_date = from_date
        while current_date <= to_date:
            PoemOfTheDay.objects.create(
                day=current_date,
                poem=poem,
                description="Tato báseň byla vybrána náhodně."
            )
            self.stdout.write(self.style.SUCCESS(f'PoemOfTheDay created for {current_date}'))
            current_date += timedelta(days=1)
