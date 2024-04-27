import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Book, PoemInCCV, Poem

class Command(BaseCommand):
    help = 'Imports CCV Poem Parts from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            with transaction.atomic():
                k = 0
                for row in reader:
                    k +=1
                    if k >= 1000:
                        pass
                    poem_in_cek = Poem.objects.get(id=int(row.get('id')))
                    book_in_cek = Book.objects.get(id=int(row.get('ccv_book_id')))
                    cek_part_of = None
                    if row.get('cek_part_of'):
                        cek_part_of = Poem.objects.get(id = int(row.get('cek_part_of')))
                    cek_next_issue_of = None
                    if row.get('cek_next_issue_of'):
                        cek_next_issue_of = Poem.objects.get(id = int(row.get('cek_next_issue_of')))
                    year = row['ccv_year'] if row['ccv_year'] and row['ccv_year'] != 'neuveden' else None
                    if year is not None and year[0] == '[':
                        year = year[1:-1]
                    PoemInCCV.objects.create(
                        poem_in_cek = poem_in_cek,
                        book_in_cek = book_in_cek,
                        cluster_id = row['ccv_id'] if row['ccv_id'] else None,
                        ccv_id = row['ccv_poem_id'] if row['ccv_poem_id'] else None,
                        ccv_title = row['ccv_title'] if row['ccv_title'] else None,
                        ccv_author = row['ccv_author'] if row['ccv_author'] else None,
                        ccv_year = year,
                        ccv_part_of = row['ccv_part_of'] if row['ccv_part_of'] else None,
                        ccv_part_order = row['ccv_part_order'] if row['ccv_part_order'] else None,
                        ccv_next_issue_of = row['ccv_next_issue_of'] if row['ccv_next_issue_of'] else None,
                        cek_part_of = cek_part_of,
                        cek_next_issue_of = cek_next_issue_of
                    )
        self.stdout.write(self.style.SUCCESS('Successfully imported ccv poem parts.'))