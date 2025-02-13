import json
import os
from django.core.management.base import BaseCommand
from web.models import Entity, EntityOccurrence, PoemAIText

class Command(BaseCommand):
    help = "Erase all 'Place' entities and their occurrences, then import entities from JSON."

    def handle(self, *args, **options):
        json_path = os.path.join('web', 'data', 'entities.json')

        # Step 1: Erase all "Place" entities and their occurrences
        self.stdout.write(self.style.WARNING("Deleting all 'Place' entities and their occurrences..."))
        place_entities = Entity.objects.filter(type=Entity.PLACE)
        deleted_count, _ = place_entities.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} place entities and related occurrences."))

        # Step 2: Load the JSON file
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR("JSON file not found. Aborting."))
            return

        with open(json_path, 'r', encoding='utf-8') as json_file:
            entity_data = json.load(json_file)

        # Step 3: Save data to the models
        self.stdout.write(self.style.WARNING("Importing entities from JSON..."))

        for wiki_id, data in entity_data.items():
            # Create or update the Entity
            entity, created = Entity.objects.update_or_create(
                wiki_id=wiki_id,
                defaults={
                    "lemma": data.get("lemma", ""),
                    "lemma_en": data.get("lemma_en", ""),
                    "type": Entity.PLACE,  # Since we are only importing "Place" entities
                    "wiki_link": data.get("wiki_link", ""),
                    "wiki_link_en": data.get("wiki_link_en", ""),
                    "summary": data.get("summary", ""),
                    "summary_en": data.get("summary_en", ""),
                    "to_index": True,  # Defaulting to True
                }
            )

            # Create occurrences for this entity
            occurrences = data.get("occurrences", [])
            for occ in occurrences:
                poem_ai_text = PoemAIText.objects.filter(id=occ["poem_ai_text_id"]).first()
                if poem_ai_text:
                    EntityOccurrence.objects.create(
                        poem_ai_text=poem_ai_text,
                        entity=entity,
                        word_id=occ["word_id"],
                        length=occ["length"],
                        tokens=occ["tokens"],
                    )
            self.stdout.write(self.style.SUCCESS(f"Entity {wiki_id} imported."))

        self.stdout.write(self.style.SUCCESS("Entities and occurrences successfully imported!"))
