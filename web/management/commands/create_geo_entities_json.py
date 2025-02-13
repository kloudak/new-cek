import json
import os
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from web.models import PoemAIText
from web.utils import get_wikipedia_info

class Command(BaseCommand):
    help = "Process PoemAIText to extract geographical entities and optionally create JSON."

    def add_arguments(self, parser):
        parser.add_argument('--create-json', action='store_true', help="Generate JSON with entity occurrences")
        parser.add_argument('--download-wiki', action='store_true', help="Download Wiki descriptions")

    def handle(self, *args, **options):
        create_json = options['create_json']
        download_wiki = options['download_wiki']

        if create_json:
            # Dictionary to store extracted entity occurrences
            entity_dict = {}

            # Go through all PoemAIText instances
            for poem_ai_text in PoemAIText.objects.all().order_by('poem__id'): # PoemAIText.objects.filter(poem__id=109600003)
                self.stdout.write(self.style.NOTICE(f"Processing poem id {poem_ai_text.poem.id}"))
                text = poem_ai_text.text
                if not text or 'd-geo="1"' not in text:
                    continue  # Skip if there's no geographical entity

                # Parse HTML (note: no root element)
                soup = BeautifulSoup(text, 'html.parser')
                n_words = 0
                for word in soup.find_all('w', attrs={'d-geo': '1'}):
                    n_words += 1
                    wiki_id = word.get('d-geo-wiki')
                    if not wiki_id:
                        continue  # Skip words without d-geo-wiki (they are part of a multi-word entity)

                    # Get the word ID and tokens
                    word_id = word.get('id')
                    tokens = [word.get_text()]
                    length = 1

                    # Collect following words of the same entity
                    next_sibling = word.find_next_sibling()
                    while next_sibling and next_sibling.name == 'w' and next_sibling.get('d-geo') == '1' and not next_sibling.get('d-geo-wiki'):
                        tokens.append(next_sibling.get_text())
                        length += 1
                        next_sibling = next_sibling.find_next_sibling()

                    # Store entity information
                    if wiki_id not in entity_dict:
                        entity_dict[wiki_id] = {
                            'id': None,
                            'lemma': None,
                            'type': 'Place',
                            'description': None,
                            'occurrences': []
                        }

                    # Add occurrence
                    entity_dict[wiki_id]['occurrences'].append({
                        'poem_ai_text_id': poem_ai_text.id,
                        'word_id': word_id,
                        'length': length,
                        'tokens': ' '.join(tokens),
                    })
                print(f"Found {n_words} entites.")

            # Handle JSON creation
            output_path = os.path.join('web', 'data', 'entities.json')
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(entity_dict, json_file, ensure_ascii=False, indent=4)
            self.stdout.write(self.style.SUCCESS(f'JSON saved to {output_path}'))

        # Handle downloading Wiki descriptions (placeholder for future logic)
        if download_wiki:
            json_path = os.path.join('web', 'data', 'entities.json')

            # Check if the JSON file exists
            if not os.path.exists(json_path):
                self.stdout.write(self.style.ERROR("JSON file not found. Aborting."))
                return

            # Load existing data
            with open(json_path, 'r', encoding='utf-8') as json_file:
                entity_dict = json.load(json_file)

            # Process each entity with a wiki_id
            for wiki_id, entity_data in entity_dict.items():
                if wiki_id and not entity_dict.get("lemma"):
                    self.stdout.write(self.style.NOTICE(f"Processing entity {wiki_id}"))
                    try:
                        wiki_info = get_wikipedia_info(wiki_id)

                        # Update dictionary with Wikipedia data
                        entity_data["lemma"] = wiki_info["cs"]["title"]
                        entity_data["wiki_link"] = wiki_info["cs"]["url"]
                        entity_data["summary"] = wiki_info["cs"]["summary"]
                        entity_data["lemma_en"] = wiki_info["en"]["title"]
                        entity_data["wiki_link_en"] = wiki_info["en"]["url"]
                        entity_data["summary_en"] = wiki_info["en"]["summary"]

                        entity_dict[wiki_id] = entity_data

                        # Save updated data back to JSON file
                        with open(json_path, 'w', encoding='utf-8') as json_file:
                            json.dump(entity_dict, json_file, ensure_ascii=False, indent=4)
                    except:
                        self.stdout.write(self.style.ERROR(f"Something wrong with {wiki_id}"))            
            self.stdout.write(self.style.SUCCESS(f'Updated Wikipedia information saved to {json_path}'))
