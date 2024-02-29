import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Book

class Command(BaseCommand):
    help = 'Imports Books from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            with transaction.atomic():
                for row in reader:
                    Book.objects.create(
                        id=row['id'] if 'id' in row and row['id'] else None,
                        title=row['title'] if 'title' in row and row['title'] else None,
                        author_of_motto=row['author_of_motto'] if 'author_of_motto' in row and row['author_of_motto'] else None,
                        author_xml=row['author_xml'] if 'author_xml' in row and row['author_xml'] else None,
                        dedication=row['dedication'] if 'dedication' in row and row['dedication'] else None,
                        description=row['description'] if 'description' in row and row['description'] else None,
                        edition=row['edition'] if 'edition' in row and row['edition'] else None,
                        editorial_note=row['editorial_note'] if 'editorial_note' in row and row['editorial_note'] else None,
                        format=row['format'] if 'format' in row and row['format'] else None,
                        motto=row['motto'] if 'motto' in row and row['motto'] else None,
                        pages=row['pages'] if 'pages' in row and row['pages'] else None,
                        place_of_publication=row['place_of_publication'] if 'place_of_publication' in row and row['place_of_publication'] else None,
                        publisher=row['publisher'] if 'publisher' in row and row['publisher'] else None,
                        source_signature=row['source_signature'] if 'source_signature' in row and row['source_signature'] else None,
                        subtitle=row['subtitle'] if 'subtitle' in row and row['subtitle'] else None,
                        year=row['year'] if 'year' in row and row['year'] else None
                    )

        self.stdout.write(self.style.SUCCESS('Successfully imported books'))