from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page
from django.urls import reverse
from django.template import loader
from .models import Person, Book, Authorship, Poem, PoemOfTheDay, PoemInCluster, PoemInCCV, Clustering, Cluster
from .utils import years_difference
import datetime, json, pickle, os, re, logging

cache_exp = 30 * 24 * 60 * 60
# Get the logger
search_logger = logging.getLogger('search_logger')

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
@cache_page(cache_exp)
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
@cache_page(cache_exp)
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
    next_issues = None
    issue_of = None
    poemsCCV = PoemInCCV.objects.filter(poem_in_cek_id=poem.id).filter(ccv_part_of=models.F('cluster_id')).all()
    if len(poemsCCV) > 0:
        poemCCV = poemsCCV[0]
        next_issues = list(set([p.cek_part_of for p in PoemInCCV.objects\
                                .filter(cek_next_issue_of=poemCCV.cek_next_issue_of).all()]))    
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(request, "web/poem_text.html", {
        "poem" : poem,
        "next_issues" : next_issues,
        "issue_of" : issue_of,
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
    metre = {
        "A" : "Amfibrach",
        "D" : "Daktyl",
        "J" : "Jamb",
        "N" : "Neurčeno",
        "T" : "Trochej",
        "X" : "Daktylotrochej",
        "Y" : "Daktylotrochej s předrážkou",
        "H" : "Hexametr",
    }
    try: 
        versology_stats = json.loads(poem.versology_stats)
    except:
        versology_stats = None
    return render(request, "web/poem_versology.html", {
        "poem" : poem,
        "show_text" : show_text,
        "versology_stats" : versology_stats,
        "metre": metre
    })

def poem_AI(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    try:
        poem_in_cluster = PoemInCluster.objects.get(poem_id=poem.id)
        
        ranked_poems = PoemInCluster.objects.filter(cluster=poem_in_cluster.cluster).order_by("-score")
        k = 1
        for p in ranked_poems:
            if p.poem.id == poem_in_cluster.poem.id:
                poem_in_cluster.rank = k
                break
            k += 1
        
        # TODO: I failed to use DB to get the order of the poem
    except:
        poem_in_cluster = None
    poem_count = None
    if poem_in_cluster:
        poem_count = PoemInCluster.objects.filter(cluster=poem_in_cluster.cluster).count()

    return render(request, "web/poem_AI.html", {
        "poem" : poem,
        "show_text" : show_text,
        "poem_in_cluster" : poem_in_cluster,
        "poem_count" : poem_count
    })
# SEARCH
def search(request):
    query = None
    max_results = 50 # SETTING
    if 'q' in request.GET and len(request.GET['q'].strip()) > 0:
        query = request.GET['q'].strip()
        search_logger.info(f"[F] {query}")
    if query is None:
        return redirect('index')
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

# CLUSTERING
@cache_page(cache_exp)
def clustering(request):
    clustering = Clustering.objects.get(id=3)    
    clusters = Cluster.objects.filter(clustering=clustering).annotate(num_poems=models.Count('poems'))

    return render(request, "web/clustering.html", {
        "clusters" : clusters
    })

@cache_page(cache_exp)
def cluster_detail(request, id):
    cluster = get_object_or_404(Cluster, id=id)
    poems_in_cluster = PoemInCluster.objects.filter(cluster_id=id).order_by('-score')
    total_poems = poems_in_cluster.count()
    authors_with_counts = poems_in_cluster.values(author=models.F('poem__author')).annotate(
        poem_count=models.Count('poem__author'),
        percentage=models.ExpressionWrapper(
            (models.Count('poem__author') * 100.0 / total_poems),
            output_field=models.FloatField()
        )
    ).order_by('-poem_count')
    authors_in_cluster = []
    for author_with_count in authors_with_counts:
        author = Person.objects.get(id=author_with_count['author'])
        authors_in_cluster.append({
            'author': author,
            'poem_count': author_with_count['poem_count'],
            'percentage': author_with_count['percentage']
        })
    total_authors = len(authors_in_cluster)
    return render(request, "web/cluster_detail.html", {
        "cluster" : cluster,
        "poems_in_cluster" : poems_in_cluster[:100],
        "total_poems" : total_poems,
        "authors_in_cluster" : authors_in_cluster[:10],
        "total_authors" : total_authors
    })

# ADVANCED SEARCH
def advanced_search(request):
    # authors
    authors = Person.objects.annotate(num_books=models.Count('authorships')).filter(num_books__gt=0)
    # books
    cache_file = 'web/__mycache__/books_list.pkl'
    books = None
    try:
        with open(cache_file, 'rb') as file:
            books = pickle.load(file)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        books = Book.objects.annotate(num_authors=models.Count('authors')).order_by('title')
        for book in books:
            authors_count = book.num_authors
            if authors_count == 1:
                author = book.authors.first()
                book.display_authors = f"{author.surname} {author.firstname}"
            else:
                book.display_authors = f"{authors_count} autorů"
        
        # Ensure the cache directory exists
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Save the data to the cache file
        with open(cache_file, 'wb') as file:
            pickle.dump(books, file)
    # years
    years_asc = Book.objects.values('year').annotate(num_books=models.Count('id')).filter(year__isnull=False).order_by('year')
    years_desc = Book.objects.values('year').annotate(num_books=models.Count('id')).filter(year__isnull=False).order_by('-year')
    

    return render(request, "web/advanced_search.html", {
        "authors" : authors,
        "years_asc" : years_asc,
        "years_desc" : years_desc,
        "books": books,
    })

@csrf_protect
def advanced_search_results(request):
    if request.method == 'POST':
        max_results = 200 # TODO: config
        min_books_fulltext_first = 500 # TODO: config

        selected_books = request.POST.get('selected-books', '').strip()
        poem_fulltext = request.POST.get('poem-fulltext', '').strip()

        # Validate selected-books
        if selected_books == "":
            return JsonResponse({"code": 1, "num_poems": 0, "poems": []})
        
        if not re.match(r'^\d+(,\d+)*$', selected_books):
            return JsonResponse({"code": -1, "num_poems": 0, "poems": []})
        
        # Convert selected_books to a list of integers
        book_ids = [int(id) for id in selected_books.split(',') if id.isdigit() and int(id) >= 0]

        combined_results = []
        seen_poem_ids = set()

        # log query
        if poem_fulltext:
            search_logger.info(f"[A] {poem_fulltext}")

        # Further filter poems by poem_fulltext if provided
        if len(book_ids) > min_books_fulltext_first and poem_fulltext:
            title_matches = Poem.objects.filter(title__icontains=poem_fulltext)
            for poem in title_matches:
                if poem.book.id in book_ids and poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Filter text search vector matches
            text_search_vector_matches = (Poem.objects
                        .filter(text_search_vector=poem_fulltext)
                        .annotate(
                            rank=SearchRank('text_search_vector', poem_fulltext)
                        )
                        .order_by("-rank"))
            print(len(text_search_vector_matches))
            for poem in text_search_vector_matches:
                if poem.book.id in book_ids and poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)
            # Limit the results to the first max_results entries
            num_poems = len(combined_results)
            combined_results = combined_results[:max_results]
        elif poem_fulltext:
            # Filter poems by book_ids
            poems = Poem.objects.filter(book__id__in=book_ids)
            # Search in title
            title_matches = poems.filter(title__icontains=poem_fulltext)
            for poem in title_matches:
                if poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Filter text search vector matches
            search_query = SearchQuery(poem_fulltext)
            text_search_vector_matches = (poems
                .filter(text_search_vector=poem_fulltext)
                .annotate(
                    rank=SearchRank('text_search_vector', poem_fulltext)
                )
                .order_by("-rank"))
            for poem in text_search_vector_matches:
                if poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Limit the results to the first max_results entries
            num_poems = len(combined_results)
            combined_results = combined_results[:max_results]
        else:
            poems = Poem.objects.filter(book__id__in=book_ids)
            num_poems = len(poems)
            combined_results = list(poems[:max_results])

        # Prepare the response data
        response_data = {
            "code": 1,
            "num_poems": num_poems,
            "max_results" : max_results,
            "poems": [
                {
                    "title": poem.title,
                    "book_title": f"{poem.book}",
                    "author": f"{poem.book.authorships.first().person.firstname} {poem.book.authorships.first().person.surname}" if poem.book and poem.book.authorships.exists() else "",
                    "link":  reverse('poem_text', kwargs={'id': poem.id})
                }
                for poem in combined_results
            ]
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({"code": -1}, status=400)

# STATIC PAGES
def about_project(request):
    return render(request, "web/about_project.html")

def personal_data(request):
    return render(request, "web/personal_data.html")

def for_schools(request):
    return render(request, "web/for_schools.html")

def editors(request):
    return render(request, "web/editors.html")

def editorial_note(request):
    return render(request, "web/editorial_note.html")

def robots(request):
    template = loader.get_template('web/robots.txt')
    return HttpResponse(template.render(), content_type='text/plain')