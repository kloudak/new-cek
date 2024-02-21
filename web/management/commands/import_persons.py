import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Person

class Command(BaseCommand):
    help = 'Imports persons from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            with transaction.atomic():
                for row in reader:
                    pseudonym_for = None
                    # Check if pseudonym_for_id is present and is a valid integer
                    if row.get('pseudonym_for_id'):
                        try:
                            pseudonym_for_id = int(row['pseudonym_for_id'])
                            pseudonym_for = Person.objects.get(id=pseudonym_for_id)
                        except ValueError:
                            # Handle case where pseudonym_for_id is not a valid integer
                            self.stdout.write(self.style.WARNING(f"Importing {row['id']} : {row['surname']}: Invalid pseudonym_for_id '{row['pseudonym_for_id']}' skipped."))
                            continue
                        except Person.DoesNotExist:
                            # Handle case where no Person matches the pseudonym_for_id
                            self.stdout.write(self.style.ERROR(f"Importing {row['id']} : {row['surname']}: Person with id {pseudonym_for_id} does not exist."))
                            continue

                    Person.objects.create(
                        id=row['id'] if row['id'] else None,
                        firstname=row['firstname'],
                        surname=row['surname'],
                        date_of_birth=row['date_of_birth'] if row['date_of_birth'] else None,
                        date_of_death=row['date_of_death'] if row['date_of_death'] else None,
                        place_of_birth=row['place_of_birth'],
                        place_of_death=row['place_of_death'],
                        place_of_birth_original_name=row['place_of_birth_original_name'],
                        place_of_death_original_name=row['place_of_death_original_name'],
                        remark=row['remark'],
                        sex=row['sex'],
                        pseudonym_for=pseudonym_for
                    )

        self.stdout.write(self.style.SUCCESS('Successfully imported persons'))