import csv, os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Book, PoemInCCV, Poem, PoemAIText

class Command(BaseCommand):
    help = 'Imports CCV Poem Parts from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str)

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Use a transaction to ensure data integrity
            k = 0
            directory = "web/data/poem_texts"
            source_directory = "web/data/_poem_texts"
            for row in reader:
                k +=1
                if k >= 100:
                    # continue
                    pass
                cekid = row.get('id')
                poem = Poem.objects.get(id=cekid)
                ccv_poems = [p.cluster_id for p in poem.poems_in_ccv.all()]
                content = ""
                for cid in ccv_poems:
                    cid_with_zero = str(cid).zfill(6)
                    filename = os.path.join(source_directory, f"{cid_with_zero}.html")
                    # 1. Read content of the file if it exists and append it to the `content` variable
                    if os.path.exists(filename):
                        with open(filename, 'r', encoding='utf-8') as file:
                            content += file.read()
                    else:
                        print(f"File {filename} does not exist. Skipping.")

                # 3. Save the `content` variable to a new file
                # new_filename = os.path.join(directory, f"{cekid}.html")
                # with open(new_filename, 'w', encoding='utf-8') as new_file:
                #    new_file.write(content)
                
                PoemAIText.objects.update_or_create(
                    poem=poem,  # Look for an existing instance with this poem
                    defaults={'text': content}  # Update text field or create with this value
                )

                print(f"Text updated for poem #{poem.id}")