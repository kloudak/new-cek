import json, pickle
from django.core.management.base import BaseCommand
from collections import defaultdict
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
        author_books_js = f"var author_book = {json.dumps(author_books)};\n\n"

        # publishers, place_of_publication, edition
        books = Book.objects.all()
        
        publishers = {}
        publisher_book = defaultdict(list)
        publisher_id_counter = 1
        publisher_to_id = {}


        place_of_publications = {}
        place_of_publication_book = defaultdict(list)
        place_of_publication_id_counter = 1
        place_of_publication_to_id = {}

        editions = {}
        edition_book = defaultdict(list)
        edition_id_counter = 1
        edition_to_id = {}

        author_of_mottos = {}
        author_of_motto_book = defaultdict(list)
        author_of_motto_id_counter = 1
        author_of_motto_to_id = {}
        
        for book in books:
            # publisher
            publisher = book.publisher
            if not publisher:
                continue
            if publisher not in publisher_to_id:
                publisher_to_id[publisher] = publisher_id_counter
                publishers[publisher_id_counter] = publisher
                publisher_id_counter += 1
            pub_id = publisher_to_id[publisher]
            publisher_book[pub_id].append(book.id)
            
            # place of publication
            place_of_publication = book.place_of_publication
            if not place_of_publication:
                continue
            if place_of_publication not in place_of_publication_to_id:
                place_of_publication_to_id[place_of_publication] = place_of_publication_id_counter
                place_of_publications[place_of_publication_id_counter] = place_of_publication
                place_of_publication_id_counter += 1
            pub_id = place_of_publication_to_id[place_of_publication]
            place_of_publication_book[pub_id].append(book.id)

            # edition
            edition = book.edition
            if not edition:
                continue
            if edition not in edition_to_id:
                edition_to_id[edition] = edition_id_counter
                editions[edition_id_counter] = edition
                edition_id_counter += 1
            pub_id = edition_to_id[edition]
            edition_book[pub_id].append(book.id)

            # author_of_motto
            author_of_motto = book.author_of_motto
            if not author_of_motto:
                continue
            if author_of_motto not in author_of_motto_to_id:
                author_of_motto_to_id[author_of_motto] = author_of_motto_id_counter
                author_of_mottos[author_of_motto_id_counter] = author_of_motto
                author_of_motto_id_counter += 1
            pub_id = author_of_motto_to_id[author_of_motto]
            author_of_motto_book[pub_id].append(book.id)
        
        # publisher
        publisher_book = dict(publisher_book)
        publishers_js = f"var publishers = {publishers};\n\n"
        publisher_book_js = f"var publisher_book = {publisher_book}\n\n;"
        # place of publication
        place_of_publication_book = dict(place_of_publication_book)
        place_of_publications_js = f"var place_of_publications = {place_of_publications};\n\n"
        place_of_publication_book_js = f"var place_of_publication_book = {place_of_publication_book}\n\n;"
        # edition
        edition_book = dict(edition_book)
        editions_js = f"var editions = {editions};\n\n"
        edition_book_js = f"var edition_book = {edition_book}\n\n;"
        # author_of_motto
        author_of_motto_book = dict(author_of_motto_book)
        author_of_mottos_js = f"var author_of_mottos = {author_of_mottos};\n\n"
        author_of_motto_book_js = f"var author_of_motto_book = {author_of_motto_book}\n\n;"

        # Write the JSON to the file search-data.js
        with open('web/static/web/js/search-data.js', 'w+') as file:
            file.write(f'''
{author_books_js} 
{publishers_js} 
{publisher_book_js}
{place_of_publications_js} 
{place_of_publication_book_js}
{editions_js} 
{edition_book_js}
{author_of_mottos_js} 
{author_of_motto_book_js}
                       ''')

        self.stdout.write(self.style.SUCCESS('Successfully exported author-book relationships to search-data.js'))