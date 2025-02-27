import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from web.models import Entity, EntityOccurrence, PoemAIText, Poem
from web.utils import get_wikipedia_info

class Command(BaseCommand):
    help = 'Manage person entities and optionally load Wikipedia data'

    def add_arguments(self, parser):
        parser.add_argument('--load_wiki', action='store_true', help='Load Wikipedia data for entities')
        parser.add_argument('--mark_occurences', action='store_true', help='Mark occurrences in text')

    def handle(self, *args, **options):
        load_wiki = options['load_wiki']
        mark_occurences = options['mark_occurences']

        if load_wiki:
            persons_with_wiki = Entity.objects.filter(type=Entity.PERSON).exclude(wiki_id='')
            self.stdout.write(self.style.SUCCESS(f'Loading Wikipedia data for {len(persons_with_wiki)} Person entities...'))
            
            for entity in persons_with_wiki:
                self.stdout.write(self.style.NOTICE(f'Getting data for entity {entity.lemma} with Wiki ID {entity.wiki_id}'))
                wiki_info = get_wikipedia_info(entity.wiki_id)
                if wiki_info:
                    entity.wiki_link = wiki_info.get("cs", {}).get("url", '')
                    entity.summary = wiki_info.get("cs", {}).get("summary", '')
                    entity.lemma_en = wiki_info.get("en", {}).get("title", '')
                    entity.wiki_link_en = wiki_info.get("en", {}).get("url", '')
                    entity.summary_en = wiki_info.get("en", {}).get("summary", '')
                    entity.save()
            
            self.stdout.write(self.style.SUCCESS('Updated Wikipedia data for entities.'))
        
        if mark_occurences:
            self.stdout.write(self.style.SUCCESS('Marking occurrences in text...'))
            
            poems = Poem.objects.filter(entities_done=True)
            
            for poem in poems:
                poem_ai_text = PoemAIText.objects.filter(poem=poem).first()
                if not poem_ai_text or not poem_ai_text.text:
                    continue
                self.stdout.write(self.style.NOTICE(f'Processing poem {poem.id}'))
                
                text = f"<root>{poem_ai_text.text}</root>"  # Temporarily wrap in a root element
                try:
                    root = ET.fromstring(text)
                except ET.ParseError:
                    self.stderr.write(self.style.ERROR(f'Error parsing XML for poem {poem.id}'))
                    continue
                
                # Remove existing d-person and d-person-wiki attributes
                for word in root.findall('.//w'):
                    if 'd-person' in word.attrib:
                        del word.attrib['d-person']
                    if 'd-person-wiki' in word.attrib:
                        del word.attrib['d-person-wiki']
                
                # Fetch occurrences and mark them
                occurrences = EntityOccurrence.objects.filter(poem_ai_text=poem_ai_text, entity__type=Entity.PERSON, entity__to_index=True)
                words = {w.attrib['id']: w for w in root.findall('.//w')}
                
                for occurrence in occurrences:
                    if occurrence.word_id in words:
                        word = words[occurrence.word_id]
                        word.set('d-person', '1')
                        word.set('d-person-wiki', occurrence.entity.wiki_id)
                        
                        # Add d-person="1" to subsequent words if length > 1
                        next_word_id = occurrence.word_id
                        for _ in range(occurrence.length - 1):
                            next_word_id_parts = next_word_id.split('-')
                            next_word_id_parts[-1] = str(int(next_word_id_parts[-1]) + 1)
                            next_word_id = '-'.join(next_word_id_parts)
                            if next_word_id in words:
                                words[next_word_id].set('d-person', '1')
                
                # Save updated XML back to the database without the temporary root
                poem_ai_text.text = ''.join(ET.tostring(root, encoding='unicode').split('<root>')[1:]).rsplit('</root>', 1)[0]
                poem_ai_text.save()
            
            self.stdout.write(self.style.SUCCESS('Occurrences marked successfully.'))
        
        self.stdout.write(self.style.SUCCESS('Command execution completed.'))