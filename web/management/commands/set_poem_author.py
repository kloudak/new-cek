from django.core.management.base import BaseCommand, CommandError
from web.models import Poem, Book
import os
import glob

class Command(BaseCommand):
    help = 'Go throught all poems and set its author to the author of the book (if unique).'

    def handle(self, *args, **options):
        books = Book.objects.all().order_by('id')

        for book in books:
            self.stdout.write(self.style.SUCCESS(f"Processing book id = {book.id}"))
            # if the book has unique author set him/her as the author of all its poems
            if len(book.authors.all()) == 1:
                for poem in book.poems.all():
                    if poem.author is not None:
                        continue
                    poem.author = book.authors.first()
                    poem.save()
            else: 
                self.stdout.write(self.style.ERROR(f"Skipping ... it has more than one author."))