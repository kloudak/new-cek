from django.http import HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from .models import Person, Book, Authorship, Poem, PoemOfTheDay
from .utils import years_difference
import datetime

def index(request):
    n_books = Book.objects.count()
    n_authors = Person.objects.count()
    poem_of_today = PoemOfTheDay.objects.filter(day = timezone.localtime().date()).first()
    poem_of_today.set_poem_text()
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
    show_text = False
    if book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= book.public_domain_year
    return render(request, "web/book_detail.html", {
        "book" : book,
        "show_text" : show_text
    })

# POEMS
def poem_text(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(request, "web/poem_text.html", {
        "poem" : poem,
        "show_text" : show_text
    })

def poem_in_book(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    poems_in_book = poem.book.poems.all().order_by('order_in_book')
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(request, "web/poem_in_book.html", {
        "poem" : poem,
        "poems_in_book" : poems_in_book,
        "show_text" : show_text
    })

def poem_versology(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(request, "web/poem_versology.html", {
        "poem" : poem,
        "show_text" : show_text
    })

def poem_AI(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(request, "web/poem_AI.html", {
        "poem" : poem,
        "show_text" : show_text
    })
# SEARCH
def search(request):
    query = None
    max_results = 50 # SETTING
    if 'q' in request.GET and len(request.GET['q'].strip()) > 0:
        query = request.GET['q'].strip()
    if query is None:
        redirect('index')
    # search in authors name
    authors = Person.objects.filter(
        models.Q(firstname__icontains=query) | models.Q(surname__icontains=query)
    )
    # search in book titles
    books_title = Book.objects.filter(title__icontains=query)
    books_fulltext = []
    if books_title.count() < max_results:
        limit = max_results - books_title.count()
        books_fulltext = Book.objects.exclude(id__in=books_title.values('id')).\
            filter(text_search_vector=query).\
            annotate(
                rank=SearchRank('text_search_vector', query)
            ).\
            order_by("-rank")[:limit]
    books = list(books_title) + list(books_fulltext)
    # search in poems titles
    poems_title = Poem.objects.filter(title__icontains=query)
    poems_fulltext = []
    if poems_title.count() < max_results:
        limit = max_results - poems_title.count()
        poems_fulltext = Poem.objects.exclude(id__in=poems_title.values('id')).\
            filter(text_search_vector=query).\
            annotate(
                rank=SearchRank('text_search_vector', query)
            ).\
            order_by("-rank")[:limit]
    poems = list(poems_title) + list(poems_fulltext)
    return render(request, "web/search_results.html", {
        "query": query,
        "authors" : authors,
        "poems" : poems,
        "books" : books,
        "max_results" : max_results,
    })

# ADVANCED SEARCH
def advanced_search(request):
    return render(request, "web/advanced_search.html")

# STATIC PAGES
def about_project(request):
    return render(request, "web/about_project.html")

def personal_data(request):
    return render(request, "web/personal_data.html")

def for_schools(request):
    return render(request, "web/for_schools.html")