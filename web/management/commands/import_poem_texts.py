from django.core.management.base import BaseCommand, CommandError
from web.models import Poem
import os
import glob

class Command(BaseCommand):
    help = 'Imports poem texts from files into the Poem model'

    def add_arguments(self, parser):
        parser.add_argument('datadir', type=str, help='Directory containing files to import')

    def handle(self, *args, **options):
        datadir = options['datadir']
        xml_files = glob.glob(os.path.join(datadir, 'poem_*.xml'))

        if not xml_files:
            self.stdout.write(self.style.WARNING('No files found in the specified directory.'))
            return

        for xml_file in xml_files:
            self.stdout.write(f'Processing {xml_file}...')
            
            # Extract poem_id from the file name
            poem_id = os.path.basename(xml_file).split('_')[1].split('.')[0]

            try:
                poem_id = int(poem_id)
            except ValueError:
                self.stdout.write(self.style.ERROR(f'Invalid poem_id "{poem_id}" extracted from file name {xml_file}.'))
                continue

            # Read the file content directly
            try:
                with open(xml_file, 'r', encoding='utf-8') as file:
                    poem_text = file.read()
            except IOError as e:
                self.stdout.write(self.style.ERROR(f'Error reading file {xml_file}: {e}'))
                continue

            # Update Poem model
            try:
                poem = Poem.objects.get(id=poem_id)
                poem.text = poem_text
                poem.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully updated Poem with id {poem_id}.'))
            except Poem.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Poem with id {poem_id} does not exist.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating Poem with id {poem_id}: {e}'))
