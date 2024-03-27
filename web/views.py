from django.http import HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.db import models
from .models import Person, Book, Authorship, Poem, PoemOfTheDay
from .utils import years_difference

def index(request):
    n_books = Book.objects.count()
    n_authors = Person.objects.count()
    poem_of_today = PoemOfTheDay.objects.filter(day = timezone.localtime().date()).first()
    return render(request, "web/index.html", {
        'n_books': n_books,
        'n_authors' : n_authors,
        'pod' : poem_of_today
    })

# AUTHORS
def author_list(request):
    persons = []
    persons_without_pseudonymes = Person.objects.filter(pseudonym_for__isnull=True).annotate(
        books_authored=models.Count('authorships', distinct=True) + 
        models.Count('pseudonyms__authorships', distinct=True)
    )
    for person in persons_without_pseudonymes:
        pseudonyms_list = person.pseudonyms.all()
        books_count = person.books_authored  # This now includes count from pseudonyms as well
        persons.append({
            'person': person,
            'pseudonyms': pseudonyms_list,
            'books_count': books_count
        })
    return render(request, "web/author_list.html", {
        'persons': persons
    })

def author_detail(request, id):
    # Fetch the person and their related books directly
    author = get_object_or_404(Person, id=id)
    if author.pseudonym_for is not None:
        raise Http404()

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
    book = get_object_or_404(Book.objects.prefetch_related('authorships__person'), id=id)
    book.set_complete_text()
    return render(request, "web/book_detail.html", {
        "book" : book
    })

# POEMS
def poem_text(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    return render(request, "web/poem_text.html", {
        "poem" : poem
    })

def poem_in_book(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    poems_in_book = poem.book.poems.all().order_by('order_in_book')
    return render(request, "web/poem_in_book.html", {
        "poem" : poem,
        "poems_in_book" : poems_in_book
    })

def poem_versology(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    return render(request, "web/poem_versology.html", {
        "poem" : poem
    })

def poem_AI(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    return render(request, "web/poem_AI.html", {
        "poem" : poem
    })

# STATIC PAGES
def about_project(request):
    return render(request, "web/about_project.html")

def personal_data(request):
    return render(request, "web/personal_data.html")

def for_schools(request):
    return render(request, "web/for_schools.html")