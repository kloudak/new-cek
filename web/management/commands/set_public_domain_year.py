from django.core.management.base import BaseCommand
from web.models import Book

class Command(BaseCommand):
    help = 'Goes through all books in the database and set its public domain year.'

    def handle(self, *args, **kwargs):
        for book in Book.objects.filter(public_domain_year__isnull=True).order_by('id'):
            authorships = book.authorships.all()
            public_domain_year = 0
            not_available = False
            for authorship in authorships:
                if not_available:
                    continue
                death_year = None
                author_id = None
                if authorship.person.pseudonym_for is not None:
                    author_id = authorship.person.pseudonym_for.id
                    if authorship.person.pseudonym_for.date_of_death is not None:
                        death_year = authorship.person.pseudonym_for.date_of_death.year
                else:
                    author_id = authorship.person.id
                    if authorship.person.date_of_death is not None:
                        death_year = authorship.person.date_of_death.year
                if death_year is not None:
                    if death_year + 71 > public_domain_year:
                        public_domain_year = death_year + 71
                else:
                    not_available = True
            if len(authorships) == 1:
                if author_id == 150: # Gellner
                    public_domain_year = 1914 + 71
                    not_available = False
                elif author_id == 116: # Adolf Bohuslav Dostal
                    public_domain_year = 1939 + 71
                    not_available = False
                elif author_id ==  118: # Karel Dostál-Lutinov
                    public_domain_year = 1923 + 71
                    not_available = False
                elif author_id ==  617: # František Taufer
                    public_domain_year = 1915 + 71
                    not_available = False
                elif author_id ==  511: # Josef Rosenzweig-Moir
                    public_domain_year = 1944 + 71
                    not_available = False
            if not_available or public_domain_year == 0:
                self.stdout.write(self.style.ERROR(f'Public domain year cannot be set for book ID={book.id})'))
            else:
                book.public_domain_year = public_domain_year
                book.save()