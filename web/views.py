from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Count
from .models import Person, Book, Authorship

def index(request):
    return render(request, "web/index.html")

# AUTHORS
def author_list(request):
    persons = Person.objects.annotate(num_books=Count('authorships__book')).order_by('surname', 'firstname')
    return render(request, "web/author_list.html", {
        'persons': persons
    })

def author_detail(request, id):
    return render(request, "web/author_detail.html", {
        "id" : id
    })

# BOOKS
def book_list(request):
    return render(request, "web/book_list.html", {
        
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