from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import cache_page
from django.urls import reverse
from django.template import loader
from .models import (
    Person,
    Book,
    Authorship,
    Poem,
    PoemOfTheDay,
    PoemInCluster,
    PoemInCCV,
    Clustering,
    Cluster,
    PoemAIText,
    Entity,
    EntityOccurrence,
)
from .utils import years_difference
import datetime, json, pickle, os, re, logging
from collections import defaultdict
import unicodedata

# template cache
cache_exp = 30 * 24 * 60 * 60
# Get the logger
search_logger = logging.getLogger("search_logger")
# metres names
metre = {
    "A": "Amfibrach",
    "D": "Daktyl",
    "J": "Jamb",
    "N": "Neurčeno",
    "T": "Trochej",
    "X": "Daktylotrochej",
    "Y": "Daktylotrochej s předrážkou",
    "H": "Hexametr",
    "nodata": "<i>chybí data</i>",
}


def index(request):
    n_books = Book.objects.count()
    n_authors = Person.objects.count()
    poem_of_today = PoemOfTheDay.objects.filter(day=timezone.localtime().date()).first()
    try:
        poem_of_today.set_poem_text()
    except:
        poem_of_today.html_text = (
            '<div class="poem-text"><i>text básně se nepodařilo najít</i></div>'
        )
    return render(
        request,
        "web/index.html",
        {"n_books": n_books, "n_authors": n_authors, "pod": poem_of_today},
    )


# AUTHORS
@cache_page(cache_exp)
def author_list(request):
    persons = []
    persons_without_pseudonymes = Person.objects.filter(
        pseudonym_for__isnull=True
    ).annotate(
        books_authored=models.Count("authorships", distinct=True)
        + models.Count("pseudonyms__authorships", distinct=True)
    )
    for person in persons_without_pseudonymes:
        pseudonyms_list = person.pseudonyms.all()
        books_count = (
            person.books_authored
        )  # This now includes count from pseudonyms as well
        persons.append(
            {
                "person": person,
                "pseudonyms": pseudonyms_list,
                "books_count": books_count,
            }
        )
    return render(request, "web/author_list.html", {"persons": persons})


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
        models.Q(person_id=id) | models.Q(person__pseudonym_for_id=id)
    ).select_related("book", "person")

    # Extract unique books from the authorships
    books_dict = {}
    for authorship in authorships:
        books_dict[authorship.book.id] = authorship.book

    # Extract books from the dictionary and sort them by year
    books = sorted(
        books_dict.values(), key=lambda book: (book.year if book.year else 0)
    )

    # stats
    try:
        stats = json.loads(author.stats)
        stats["metre"] = dict(
            sorted(stats["metre"].items(), key=lambda item: item[1], reverse=True)
        )
    except:
        stats = None

    return render(
        request,
        "web/author_detail.html",
        {
            "author": author,
            "books": books,
            "pseudonyms": pseudonyms,
            "age": age,
            "stats": stats,
            "metre": metre,
        },
    )


# BOOKS
@cache_page(cache_exp)
def book_list(request):
    books = (
        Book.objects.prefetch_related("authorships__person")
        .all()
        .order_by("title", "year")
    )
    return render(request, "web/book_list.html", {"books": books})


def book_detail(request, id):
    book = get_object_or_404(
        Book.objects.prefetch_related("authorships__person"), id=id
    )
    book.set_complete_text()
    show_text = False
    if book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= book.public_domain_year
    return render(
        request,
        "web/book_detail.html",
        {
            "book": book,
            "show_text": show_text,
        },
    )


# POEMS
def poem_text(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    next_issues = None
    issue_of = None

    poemsCCV = (
        PoemInCCV.objects.filter(poem_in_cek_id=poem.id)
        .filter(ccv_next_issue_of=models.F("cluster_id"))
        .all()
    )

    if len(poemsCCV) > 0:
        poemCCV = poemsCCV[0]
        next_issues = list(
            set(
                [
                    p.poem_in_cek
                    for p in PoemInCCV.objects.filter(
                        cek_next_issue_of=poemCCV.cek_next_issue_of
                    ).all()
                ]
            )
        )

    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(
        request,
        "web/poem_text.html",
        {
            "poem": poem,
            "next_issues": next_issues,
            "issue_of": issue_of,
            "show_text": show_text,
        },
    )


def poem_in_book(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    poems_in_book = poem.book.poems.all().order_by("order_in_book")
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    return render(
        request,
        "web/poem_in_book.html",
        {"poem": poem, "poems_in_book": poems_in_book, "show_text": show_text},
    )


def poem_versology(request, id):
    poem = get_object_or_404(Poem, id=id)
    poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year
    try:
        versology_stats = json.loads(poem.versology_stats)
    except:
        versology_stats = None
    return render(
        request,
        "web/poem_versology.html",
        {
            "poem": poem,
            "show_text": show_text,
            "versology_stats": versology_stats,
            "metre": metre,
        },
    )


def poem_AI(request, id):
    poem = get_object_or_404(Poem, id=id)
    # poem.set_html_text()
    show_text = False
    if poem.book.public_domain_year is not None:
        show_text = datetime.datetime.now().year >= poem.book.public_domain_year

    poem_text = None
    poem_ai_text = PoemAIText.objects.filter(poem=poem).first()

    entities = []
    n_places = 0
    n_persons = 0
    if poem_ai_text and poem_ai_text.text:
        poem_text = f'<div class="poem-text-with-entities">{poem_ai_text.text}</div>'
        entities = Entity.objects.filter(
            occurrences__poem_ai_text=poem_ai_text, to_index=True
        ).distinct()
        for e in entities:
            if e.type == Entity.PLACE:
                n_places += 1
            elif e.type == Entity.PERSON:
                n_persons += 1
    else:
        print(f"PoemAIText for Poem {poem.id} does not exist or is empty")

    # info on cluster
    try:
        poem_in_cluster = PoemInCluster.objects.get(poem_id=poem.id)

        ranked_poems = PoemInCluster.objects.filter(
            cluster=poem_in_cluster.cluster
        ).order_by("-score")
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
        poem_count = PoemInCluster.objects.filter(
            cluster=poem_in_cluster.cluster
        ).count()

    # similar poems
    try:
        similar_poems_json = json.loads(poem.similar_poems)
        similar_poems = [
            Poem.objects.get(id=int(sp["poem_id"])) for sp in similar_poems_json
        ]
    except:
        similar_poems = None
    return render(
        request,
        "web/poem_AI.html",
        {
            "poem": poem,
            "poem_text": poem_text,
            "poem_in_cluster": poem_in_cluster,
            "poem_count": poem_count,
            "similar_poems": similar_poems,
            "show_text": show_text,
            "entities": entities,
            "n_places": n_places,
            "n_persons": n_persons,
        },
    )


# REJSTRIK
@csrf_protect
def geo_rejstrik(request):
    # Fetch all entities of type "Place" and precompute the number of poems they appear in
    places = (
        Entity.objects.filter(type=Entity.PLACE)
        .exclude(lemma__isnull=True)
        .exclude(lemma="")
        .annotate(poem_count=models.Count("occurrences__poem_ai_text", distinct=True))
        .order_by("lemma")
    )

    # Dictionary to store entities grouped by their first letter
    entity_dict = defaultdict(list)

    czech_alphabet = list("ABCČDĎEFGHIJKLŁMNŇOPQRŘSŠTŤUVWXYZŽ")

    for place in places:
        # Normalize letters with accents to base character comparison
        first_letter = place.lemma[0].upper()
        if not first_letter in czech_alphabet:
            first_letter = unicodedata.normalize("NFD", place.lemma)[0].upper()
        entity_dict[first_letter].append(place)

    # Sort dictionary keys (Czech alphabet order)
    sorted_letters = [letter for letter in czech_alphabet if letter in entity_dict]

    entity_dict = dict(
        sorted(
            entity_dict.items(),
            key=lambda x: (
                czech_alphabet.index(
                    x[0]
                )  # If the letter is in Czech alphabet, use its index
                if x[0] in czech_alphabet
                else (
                    czech_alphabet.index(unicodedata.normalize("NFD", x[0])[0].upper())
                    if unicodedata.normalize("NFD", x[0])[0].upper() in czech_alphabet
                    else len(czech_alphabet)  # If still unknown, put it at the end
                )
            ),
        )
    )

    context = {
        "type": "place",
        "entity_dict": entity_dict,
        "sorted_letters": sorted_letters,
    }
    return render(request, "web/rejstrik.html", context)

def person_rejstrik(request):
    persons = (
        Entity.objects.filter(type=Entity.PERSON).filter(to_index=True)
        .exclude(lemma__isnull=True)
        .exclude(lemma="")
        .annotate(poem_count=models.Count("occurrences__poem_ai_text", distinct=True))
        .order_by("lemma")
    )

    entity_dict = defaultdict(list)

    czech_alphabet = list("ABCČDĎEFGHIJKLŁMNŇOPQRŘSŠTŤUVWXYZŽ")

    for person in persons:
        first_letter = person.lemma[0].upper()
        if not first_letter in czech_alphabet:
            first_letter = unicodedata.normalize("NFD", person.lemma)[0].upper()
        entity_dict[first_letter].append(person)

    # Sort dictionary keys (Czech alphabet order)
    sorted_letters = [letter for letter in czech_alphabet if letter in entity_dict]

    entity_dict = dict(
        sorted(
            entity_dict.items(),
            key=lambda x: (
                czech_alphabet.index(
                    x[0]
                )  # If the letter is in Czech alphabet, use its index
                if x[0] in czech_alphabet
                else (
                    czech_alphabet.index(unicodedata.normalize("NFD", x[0])[0].upper())
                    if unicodedata.normalize("NFD", x[0])[0].upper() in czech_alphabet
                    else len(czech_alphabet)  # If still unknown, put it at the end
                )
            ),
        )
    )

    context = {
        "type": "person",
        "entity_dict": entity_dict,
        "sorted_letters": sorted_letters,
    }
    return render(request, "web/rejstrik.html", context)


def entity_detail(request, id):
    entity = get_object_or_404(Entity, id=id)

    # Determine which summary and Wikipedia link to use (prefer Czech, fallback to English)
    summary = entity.summary if entity.summary else entity.summary_en
    wiki_link = (
        entity.wiki_link
        if entity.wiki_link
        else f"https://www.wikidata.org/wiki/{entity.wiki_id}"
    )

    # Fetch all occurrences and related poems
    occurrences = (
        EntityOccurrence.objects.filter(entity=entity)
        .select_related("poem_ai_text__poem")
        .order_by("poem_ai_text__poem__author__surname", "poem_ai_text__poem__title")
    )

    # Dictionary to group poems by author
    poems_by_author = {}
    tokens = []

    for occ in occurrences:
        poem = occ.poem_ai_text.poem
        author_key = (
            f"{poem.author.surname}_{poem.author.firstname}" if poem.author else None
        )
        if author_key not in poems_by_author:
            poems_by_author[author_key] = {"author": poem.author, "poems": {}}
        if poem and author_key:
            if poem.id not in poems_by_author[author_key]["poems"]:
                poems_by_author[author_key]["poems"][poem.id] = {
                    "poem": poem,
                    "tokens": [],
                }
            if occ.tokens not in tokens:
                tokens.append(occ.tokens)

    # DEBUGGING OUTPUT (check if data exists)
    print("Entity:", entity.lemma)
    print("Poems by Author:", poems_by_author)

    context = {
        "entity": entity,
        "summary": summary,
        "wiki_link": wiki_link,
        "poems_by_author": poems_by_author,
        "tokens": tokens,
    }

    return render(request, "web/entity_detail.html", context)


# SEARCH
def search(request):
    query = None
    max_results = 50  # SETTING
    if "q" in request.GET and len(request.GET["q"].strip()) > 0:
        query = request.GET["q"].strip()
        search_logger.info(f"[F] {query}")
    if query is None:
        return redirect("index")
    # search in authors name
    authors = Person.objects.filter(
        models.Q(firstname__icontains=query) | models.Q(surname__icontains=query)
    )
    # search in book titles
    books_title = Book.objects.filter(title__icontains=query)
    books_fulltext = []
    if books_title.count() < max_results:
        limit = max_results - books_title.count()
        books_fulltext = (
            Book.objects.exclude(id__in=books_title.values("id"))
            .filter(text_search_vector=query)
            .annotate(rank=SearchRank("text_search_vector", query))
            .order_by("-rank")[:limit]
        )
    books = list(books_title) + list(books_fulltext)
    # search in poems titles
    poems_title = Poem.objects.filter(title__icontains=query)
    poems_fulltext = []
    if poems_title.count() < max_results:
        limit = max_results - poems_title.count()
        poems_fulltext = (
            Poem.objects.exclude(id__in=poems_title.values("id"))
            .filter(text_search_vector=query)
            .annotate(rank=SearchRank("text_search_vector", query))
            .order_by("-rank")[:limit]
        )
    poems = list(poems_title) + list(poems_fulltext)
    request.session["search_query"] = query
    return render(
        request,
        "web/search_results.html",
        {
            "query": query,
            "authors": authors,
            "poems": poems,
            "books": books,
            "max_results": max_results,
        },
    )


def cancel_search(request):
    if "search_query" in request.session:
        del request.session["search_query"]
    return JsonResponse({"success": True})


# CLUSTERING
@cache_page(cache_exp)
def clustering(request):
    clustering = Clustering.objects.get(id=3)
    clusters = Cluster.objects.filter(clustering=clustering).annotate(
        num_poems=models.Count("poems")
    )

    return render(request, "web/clustering.html", {"clusters": clusters})


@cache_page(cache_exp)
def cluster_detail(request, id):
    cluster = get_object_or_404(Cluster, id=id)
    poems_in_cluster = PoemInCluster.objects.filter(cluster_id=id).order_by("-score")
    total_poems = poems_in_cluster.count()
    authors_with_counts = (
        poems_in_cluster.values(author=models.F("poem__author"))
        .annotate(
            poem_count=models.Count("poem__author"),
            percentage=models.ExpressionWrapper(
                (models.Count("poem__author") * 100.0 / total_poems),
                output_field=models.FloatField(),
            ),
        )
        .order_by("-poem_count")
    )
    authors_in_cluster = []
    for author_with_count in authors_with_counts:
        author = Person.objects.get(id=author_with_count["author"])
        authors_in_cluster.append(
            {
                "author": author,
                "poem_count": author_with_count["poem_count"],
                "percentage": author_with_count["percentage"],
            }
        )
    total_authors = len(authors_in_cluster)
    return render(
        request,
        "web/cluster_detail.html",
        {
            "cluster": cluster,
            "poems_in_cluster": poems_in_cluster[:100],
            "total_poems": total_poems,
            "authors_in_cluster": authors_in_cluster[:10],
            "total_authors": total_authors,
        },
    )


# ADVANCED SEARCH
def advanced_search(request):
    # authors
    authors = Person.objects.annotate(num_books=models.Count("authorships")).filter(
        num_books__gt=0
    )
    # books
    cache_file = "web/__mycache__/books_list.pkl"
    books = None
    try:
        with open(cache_file, "rb") as file:
            books = pickle.load(file)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        books = Book.objects.annotate(num_authors=models.Count("authors")).order_by(
            "title"
        )
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
        with open(cache_file, "wb") as file:
            pickle.dump(books, file)
    # years
    years_asc = (
        Book.objects.values("year")
        .annotate(num_books=models.Count("id"))
        .filter(year__isnull=False)
        .order_by("year")
    )
    years_desc = (
        Book.objects.values("year")
        .annotate(num_books=models.Count("id"))
        .filter(year__isnull=False)
        .order_by("-year")
    )
    # clusters
    clustering = Clustering.objects.get(id=3)
    clusters_db = (
        Cluster.objects.filter(clustering=clustering)
        .annotate(num_poems=models.Count("poems"))
        .order_by("-num_poems")
    )
    clusters = {}
    for cluster in clusters_db:
        clusters[cluster.id] = {
            "description": cluster.description,
            "description_short": ", ".join((cluster.description.split(",")[0:4])),
            "num_poems": cluster.num_poems,
        }
    return render(
        request,
        "web/advanced_search.html",
        {
            "authors": authors,
            "years_asc": years_asc,
            "years_desc": years_desc,
            "books": books,
            "clusters": clusters,
        },
    )


@csrf_protect
def advanced_search_results(request):
    if request.method == "POST":
        max_results = 200  # TODO: config
        min_books_fulltext_first = 500  # TODO: config

        selected_books = request.POST.get("selected-books", "").strip()
        poem_fulltext = request.POST.get("poem-fulltext", "").strip()
        poem_clusters = request.POST.getlist("poem-clusters")

        # Validate selected-books
        if selected_books == "":
            return JsonResponse({"code": 1, "num_poems": 0, "poems": []})

        if not re.match(r"^\d+(,\d+)*$", selected_books):
            return JsonResponse({"code": -1, "num_poems": 0, "poems": []})
        try:
            book_ids = [
                int(id)
                for id in selected_books.split(",")
                if id.isdigit() and int(id) >= 0
            ]
        except ValueError:
            return JsonResponse({"code": -1, "num_poems": 0, "poems": []})

        # Validate clusters ids
        try:
            cluster_ids = [int(c) for c in poem_clusters]
        except ValueError:
            return JsonResponse({"code": -1, "num_poems": 0, "poems": []})

        combined_results = []
        seen_poem_ids = set()

        # log query
        if poem_fulltext:
            search_logger.info(f"[A] {poem_fulltext}")

        request.session["search_query"] = poem_fulltext

        # Further filter poems by poem_fulltext if provided
        if len(book_ids) > min_books_fulltext_first and poem_fulltext:
            if cluster_ids:
                title_matches = Poem.objects.filter(
                    cluster_membership__cluster_id__in=cluster_ids
                ).filter(title__icontains=poem_fulltext)
            else:
                title_matches = Poem.objects.filter(title__icontains=poem_fulltext)
            for poem in title_matches:
                if poem.book.id in book_ids and poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Filter text search vector matches
            if cluster_ids:
                text_search_vector_matches = (
                    Poem.objects.filter(cluster_membership__cluster_id__in=cluster_ids)
                    .filter(text_search_vector=poem_fulltext)
                    .annotate(rank=SearchRank("text_search_vector", poem_fulltext))
                    .order_by("-rank")
                )
            else:
                text_search_vector_matches = (
                    Poem.objects.filter(text_search_vector=poem_fulltext)
                    .annotate(rank=SearchRank("text_search_vector", poem_fulltext))
                    .order_by("-rank")
                )
            for poem in text_search_vector_matches:
                if poem.book.id in book_ids and poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)
            # Limit the results to the first max_results entries
            num_poems = len(combined_results)
            combined_results = combined_results[:max_results]
        elif poem_fulltext:
            # Filter poems by book_ids
            if cluster_ids:
                poems = Poem.objects.filter(book__id__in=book_ids).filter(
                    cluster_membership__cluster_id__in=cluster_ids
                )
            else:
                poems = Poem.objects.filter(book__id__in=book_ids)
            # Search in title
            title_matches = poems.filter(title__icontains=poem_fulltext)
            for poem in title_matches:
                if poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Filter text search vector matches
            search_query = SearchQuery(poem_fulltext)
            text_search_vector_matches = (
                poems.filter(text_search_vector=poem_fulltext)
                .annotate(rank=SearchRank("text_search_vector", poem_fulltext))
                .order_by("-rank")
            )
            for poem in text_search_vector_matches:
                if poem.id not in seen_poem_ids:
                    combined_results.append(poem)
                    seen_poem_ids.add(poem.id)

            # Limit the results to the first max_results entries
            num_poems = len(combined_results)
            combined_results = combined_results[:max_results]
        else:
            if cluster_ids:
                poems = Poem.objects.filter(book__id__in=book_ids).filter(
                    cluster_membership__cluster_id__in=cluster_ids
                )
            else:
                poems = Poem.objects.filter(book__id__in=book_ids)
            num_poems = len(poems)
            combined_results = list(poems[:max_results])

        # Prepare the response data
        response_data = {
            "code": 1,
            "num_poems": num_poems,
            "max_results": max_results,
            "poems": [
                {
                    "title": poem.title,
                    "book_title": f"{poem.book}",
                    "author": (
                        f"{poem.book.authorships.first().person.firstname} {poem.book.authorships.first().person.surname}"
                        if poem.book and poem.book.authorships.exists()
                        else ""
                    ),
                    "link": reverse("poem_text", kwargs={"id": poem.id}),
                }
                for poem in combined_results
            ],
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({"code": -1}, status=400)


# FOR SCHOOLS
def for_schools(request):
    # Get books with "for_schools=True" whose author is NULL or author's "for_schools=False"
    books = (
        Book.objects.filter(for_schools=True)
        .exclude(authorships__person__for_schools=True)
        .distinct()
        .order_by("title")
    )

    # Get authors with "for_schools=True"
    authors_query = Person.objects.filter(for_schools=True).order_by(
        "surname", "firstname"
    )

    # Create a dictionary to store authors and their books
    authors = {}
    for author in authors_query:
        # Get books for each author with "for_schools=True" ordered by year
        abooks = Book.objects.filter(
            authorships__person=author, for_schools=True
        ).order_by("title")
        authors[author] = abooks
    return render(
        request,
        "web/for_schools.html",
        {
            "books": books,
            "authors": authors,
        },
    )


# STATIC PAGES
def about_project(request):
    return render(request, "web/about_project.html")


def personal_data(request):
    return render(request, "web/personal_data.html")


def editors(request):
    return render(request, "web/editors.html")


def editorial_note(request):
    return render(request, "web/editorial_note.html")


def robots(request):
    template = loader.get_template("web/robots.txt")
    return HttpResponse(template.render(), content_type="text/plain")
