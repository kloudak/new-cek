import json, pickle
from django.core.management.base import BaseCommand
from django.db import models
from web.models import Authorship, Book

class Command(BaseCommand):
    help = 'Export data for advanced search and store them in files.'

    def handle(self, *args, **kwargs):
        # Create the dictionary { id of Person model : [ ids of all books the person is author of ]}
        author_books = {}
        for authorship in Authorship.objects.select_related('person', 'book').all():
            person_id = authorship.person.id
            book_id = authorship.book.id
            if person_id not in author_books:
                author_books[person_id] = []
            author_books[person_id].append(book_id)

        # Convert the dictionary to JSON and format it for JavaScript
        author_books_js = f'var author_book = {json.dumps(author_books)};'

        # Write the JSON to the file search-data.js
        with open('web/static/web/js/search-data.js', 'w+') as file:
            file.write(author_books_js)

        self.stdout.write(self.style.SUCCESS('Successfully exported author-book relationships to search-data.js'))