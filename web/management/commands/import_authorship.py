import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Authorship, Book, Person

class Command(BaseCommand):
    help = 'Imports Authorships from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            with transaction.atomic():
                for row in reader:
                    person_id = row['person_id']
                    book_id = row['book_id']
                    author_order = row['author_order']
                    
                    # Fetch the Person and Book instances
                    person = Person.objects.get(id=person_id)
                    book = Book.objects.get(id=book_id)
                    
                    # Create and save the Authorship instance
                    Authorship.objects.create(
                        person=person,
                        book=book,
                        author_order=author_order
                    )

        self.stdout.write(self.style.SUCCESS('Successfully imported authorship relation'))