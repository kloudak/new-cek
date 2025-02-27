import csv
import os
from django.core.management.base import BaseCommand
from web.models import Entity, EntityOccurrence, PoemAIText, Poem

class Command(BaseCommand):
    help = 'Import person entities from a CSV file'

    """
    Data are produced by the SQL:
    SELECT ep.*, e.lemma, e.type, e.wiki_link, e.to_index, p.cek_id, p.entities_done 
    FROM entity_poem ep, entity e, poem p 
    WHERE ep.id_entity = e.id AND ep.id_poem = p.id AND p.entities_done
    LIMIT 0, 1000000;
    """

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Relative path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        if not os.path.exists(csv_file_path):
            self.stderr.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        # Delete all existing Person entities
        Entity.objects.filter(type=Entity.PERSON).delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing Person entities'))

        seen_entities = {}
        seen_poems = set()

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                poem_id = row['cek_id']
                self.stdout.write(self.style.NOTICE(f'Processing poem {poem_id} with entities_done={row["entities_done"]}'))
                if not poem_id or poem_id == 'NULL':
                    continue    
                lemma = row['lemma']
                entity_type = row['type']
                to_index = row['to_index'] == '1'
                wiki_link = row['wiki_link']
                wiki_id = wiki_link.split('/')[-1] if wiki_link else ''

                # Find Poem instance
                if poem_id not in seen_poems:
                    poem = Poem.objects.filter(id=poem_id).first()
                    if poem:
                        seen_poems.add(poem_id)
                        # Set entities_done if applicable
                        if row['entities_done'] == '1':
                            poem.entities_done = True
                            poem.save()
                        else:
                            poem.entities_done = False
                            poem.save()
                else:
                    poem = Poem.objects.filter(id=poem_id).first()

                if not poem:
                    continue
                
                # Find PoemAIText instance
                poem_ai_text = PoemAIText.objects.filter(poem=poem).first()
                
                # Find or create Entity instance
                entity_key = (lemma, entity_type)
                if entity_key not in seen_entities:
                    entity, created = Entity.objects.get_or_create(
                        lemma=lemma, type=entity_type,
                        defaults={'wiki_id': wiki_id, 'to_index': to_index}
                    )
                    seen_entities[entity_key] = entity
                else:
                    entity = seen_entities[entity_key]
                
                # Create EntityOccurrence instance
                EntityOccurrence.objects.create(
                    poem_ai_text=poem_ai_text,
                    entity=entity,
                    word_id=row['word_id'],
                    length=int(row['length']),
                    tokens=row['tokens']
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully imported person entities'))
