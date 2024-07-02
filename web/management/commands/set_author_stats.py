import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from web.models import Authorship, Book, Person, Poem

class Command(BaseCommand):
    help = 'Generate stats for authors and save them to "person.stats" field as a JSON string.'

    def handle(self, *args, **options):
        persons = Person.objects.filter(pseudonym_for__isnull=True).annotate(
            books_authored=models.Count('authorships', distinct=True) + 
            models.Count('pseudonyms__authorships', distinct=True)
        )
        k = 0
        for p in persons:
            pdata = {}
            self.stdout.write(self.style.SUCCESS(f'Processing author {p}'))
            # books
            pdata['books'] = p.books_authored
            # poems
            pseudonyms = p.pseudonyms.all()
            authors = [p] + list(pseudonyms)
            poems = Poem.objects.filter(author__in=authors).distinct()
            pdata['poems'] = len(poems)
            # strophes and verses
            n_strophe = 0
            n_verses = 0
            verse_with_metre = 0
            pdata['metre'] = {}
            for poem in poems:
                n_strophe += poem.text.count('</strofa>')
                n_verses += poem.text.count('</v>')
                # metres
                vstats = json.loads(poem.versology_stats)
                if 'metre' in vstats:
                    for m, count in vstats['metre'].items():
                        verse_with_metre += count
                        if m in pdata['metre']:
                            pdata['metre'][m] += count
                        else:
                            pdata['metre'][m] = count
                pdata['metre']['nodata'] = n_verses - verse_with_metre
            pdata['strophes'] = n_strophe
            pdata['verses'] = n_verses
            p.stats = json.dumps(pdata)
            p.save()