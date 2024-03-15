import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Poem, Book

class Command(BaseCommand):
    help = 'Imports poems from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            with transaction.atomic():
                for row in reader:
                    # Check if book_id is present and is a valid integer
                    if row.get('book_id'):
                        try:
                            book_id = int(row['book_id'])
                            book = Book.objects.get(id=book_id)
                        except ValueError:
                            # Handle case where book_id is not a valid integer
                            self.stdout.write(self.style.WARNING(f"Importing book {row['id']} : Invalid book_id skipped."))
                            continue
                        except Book.DoesNotExist:
                            # Handle case where no Book matches the book_id
                            self.stdout.write(self.style.ERROR(f"Importing book {row['id']} : Book with id {book_id} does not exist."))
                            continue
                    
                    #self.stdout.write(f'Processing poem id {row['id']}...')
                    Poem.objects.create(
                        id=row['id'] if row['id'] else None,
                        title=row['title'] if row['title'] else None,
                        original_id=row['original_id'] if row['original_id'] else None,
                        order_in_book=row['order_in_book'] if row['order_in_book'] else None,
                        book=book
                    )

        self.stdout.write(self.style.SUCCESS('Successfully imported poems'))