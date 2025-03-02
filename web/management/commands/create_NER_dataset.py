import os
import csv
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from web.models import Poem, PoemAIText

DATASET_DIR = "web/data/NER-dataset/"
README_FILE = os.path.join(DATASET_DIR, "README.txt")

class Command(BaseCommand):
    help = "Create NER dataset from PoemAIText XML data"

    def handle(self, *args, **kwargs):
        os.makedirs(DATASET_DIR, exist_ok=True)
        poems = Poem.objects.filter(entities_done=True)
        poem_count = poems.count()

        with open(README_FILE, "w", encoding="utf-8") as readme:
            readme.write(f"Named Entity Recognition (NER) Dataset\n\n")
            readme.write(f"Total Poems: {poem_count}\n\n")
            readme.write("Each poem has two corresponding files:\n")
            readme.write("- {poem_id}.txt: CoNLL 2003 format representation\n")
            readme.write("- {poem_id}.csv: Token-level annotation including Wikidata IDs\n\n")
            readme.write("Structure of CSV files:\n")
            readme.write("- Column 1: token (word or punctuation)\n")
            readme.write("- Column 2: CoNLL annotation (B-LOC, I-LOC, B-PER, I-PER, O)\n")
            readme.write("- Column 3: Wikidata ID (if available)\n\n")
            readme.write("File Naming and URLs:\n")
            readme.write("- The filename corresponds to the poem ID from ceska-poezie.cz\n")
            readme.write("- The poem can be accessed at: https://www.ceska-poezie.cz/basen/{poem_id}/AI\n")
        
        for poem in poems:
            poem_ai_text = PoemAIText.objects.filter(poem=poem).first()
            if not poem_ai_text or not poem_ai_text.text:
                continue
            
            poem_id = poem.id
            txt_file_path = os.path.join(DATASET_DIR, f"{poem_id}.txt")
            csv_file_path = os.path.join(DATASET_DIR, f"{poem_id}.csv")
            
            with open(txt_file_path, "w", encoding="utf-8") as txt_file, \
                 open(csv_file_path, "w", encoding="utf-8", newline="") as csv_file:
                
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["token", "CoNLL", "wiki_id"])  # CSV header
                
                text = f"<root>{poem_ai_text.text}</root>"  # Wrap text for valid XML
                try:
                    root = ET.fromstring(text)
                except ET.ParseError:
                    self.stderr.write(self.style.ERROR(f"Failed to parse poem {poem_id}"))
                    continue
                
                for strophe in root.findall(".//strophe"):
                    for verse in strophe.findall(".//verse"):
                        for element in verse:
                            if element.tag == "w":
                                token = element.text.strip() if element.text else ""
                                entity_type = None
                                wiki_id = None
                                
                                if element.attrib.get("d-geo") == "1":
                                    entity_type = "LOC"
                                    wiki_id = element.attrib.get("d-geo-wiki", "")
                                elif element.attrib.get("d-person") == "1" or element.attrib.get("d-f-person") == "1":
                                    entity_type = "PER"
                                    wiki_id = element.attrib.get("d-person-wiki", "")
                                
                                if entity_type:
                                    # Determine if it's a B- or I- tag
                                    prev_entity = csv_writer.writerow if csv_writer else None
                                    tag = f"B-{entity_type}" if not prev_entity else f"I-{entity_type}"
                                else:
                                    tag = "O"
                                
                                # Write to files
                                txt_file.write(f"{token} {tag}\n")
                                csv_writer.writerow([token, tag, wiki_id])
                            else:
                                token = element.tail.strip() if element.tail else ""
                                if token:
                                    txt_file.write(f"{token} O\n")
                                    csv_writer.writerow([token, "O", ""])  # Non-entity token
                        
                        txt_file.write("\n")  # End of verse
                        csv_writer.writerow(["", "", ""])  # End of verse in CSV
                    txt_file.write("\n")  # End of strophe
                    csv_writer.writerow(["", "", ""])  # End of strophe in CSV
            
            self.stdout.write(self.style.SUCCESS(f"Processed poem {poem_id}"))
        
        self.stdout.write(self.style.SUCCESS("NER dataset creation complete."))
