from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Person, Book, Authorship
from .utils import years_difference

def index(request):
    return render(request, "web/index.html")

# AUTHORS
def author_list(request):
    persons = Person.objects.annotate(num_books=models.Count('authorships__book')).order_by('surname', 'firstname')
    return render(request, "web/author_list.html", {
        'persons': persons
    })

def author_detail(request, id):
    # Fetch the person and their related books directly
    author = get_object_or_404(Person, id=id)

    # Age at deathday
    if author.date_of_birth and author.date_of_death:
        age = years_difference(author.date_of_birth, author.date_of_death)
    else:
        age = None
    
    # Pseudonyms
    pseudonyms = author.pseudonyms.all()
    
    # Fetch Authorship instances where the person is a direct author or a pseudonym
    authorships = Authorship.objects.filter(
        models.Q(person_id=id) | 
        models.Q(person__pseudonym_for_id=id)
    ).select_related('book', 'person')

    # Extract unique books from the authorships
    books_dict = {}
    for authorship in authorships:
        books_dict[authorship.book.id] = authorship.book

    # Extract books from the dictionary and sort them by year
    books = sorted(books_dict.values(), key=lambda book: (book.year if book.year else 0))

    print(len(books), books)
    return render(request, 'web/author_detail.html', {
        'author': author, 
        'books': books,
        'pseudonyms': pseudonyms,
        'age': age
    })

# BOOKS
def book_list(request):
    books = Book.objects.prefetch_related('authorships__person').all().order_by('title', 'year')
    return render(request, "web/book_list.html", {
        'books' : books
    })

def book_detail(request, id):
    return render(request, "web/book_detail.html", {
        "id" : id
    })

# POEMS
def poem_text(request, id):
    return render(request, "web/poem_text.html", {
        "id" : id
    })

def poem_in_book(request, id):
    return render(request, "web/poem_in_book.html", {
        "id" : id
    })

def poem_versology(request, id):
    return render(request, "web/poem_versology.html", {
        "id" : id
    })

def poem_AI(request, id):
    return render(request, "web/poem_AI.html", {
        "id" : id
    })

# STATIC PAGES
def about_project(request):
    return render(request, "web/about_project.html")

def personal_data(request):
    return render(request, "web/personal_data.html")

def for_schools(request):
    return render(request, "web/for_schools.html")