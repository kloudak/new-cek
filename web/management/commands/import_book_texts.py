from django.core.management.base import BaseCommand, CommandError
from web.models import Book
import os
import glob

class Command(BaseCommand):
    help = 'Imports book texts from files into the Book model'

    def add_arguments(self, parser):
        parser.add_argument('datadir', type=str, help='Directory containing files to import')

    def handle(self, *args, **options):
        datadir = options['datadir']
        xml_files = glob.glob(os.path.join(datadir, 'book_*.xml'))

        if not xml_files:
            self.stdout.write(self.style.WARNING('No files found in the specified directory.'))
            return

        for xml_file in xml_files:
            self.stdout.write(f'Processing {xml_file}...')
            
            # Extract book_id from the file name
            book_id = os.path.basename(xml_file).split('_')[1].split('.')[0]

            try:
                book_id = int(book_id)
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid book_id "{book_id}" extracted from file name {xml_file}.'))
                continue

            # Read the file content directly
            try:
                with open(xml_file, 'r', encoding='utf-8') as file:
                    book_text = file.read()
            except IOError as e:
                self.stdout.write(self.style.ERROR(f'Error reading file {xml_file}: {e}'))
                continue

            # Update book model
            try:
                book = Book.objects.get(id=book_id)
                book.text = book_text
                book.save(import_xml=True)
                self.stdout.write(self.style.SUCCESS(f'Successfully updated book with id {book_id}.'))
            except book.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Book with id {book_id} does not exist.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating book with id {book_id}: {e}'))
