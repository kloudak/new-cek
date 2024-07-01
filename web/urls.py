from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # authors
    path("autori/", views.author_list, name="author_list"),
    path("autori/<int:id>", views.author_detail, name="author_detail"),
    #books
    path("knihy/", views.book_list, name="book_list"),
    path("knihy/<int:id>", views.book_detail, name="book_detail"),
    # poem views
    path("basen/<int:id>/text", views.poem_text, name="poem_text"),
    path("basen/<int:id>/v-knize", views.poem_in_book, name="poem_in_book"),
    path("basen/<int:id>/versologie", views.poem_versology, name="poem_versology"),
    path("basen/<int:id>/AI", views.poem_AI, name="poem_AI"),
    # search
    path("hledani", views.search, name="search"),
    # clustering
    path("shlukovani", views.clustering, name="clustering"),
    path("shlukovani/<int:id>", views.cluster_detail, name="cluster_detail"),
    # advanced_search
    path("badatelske-nastroje", views.advanced_search, name="advanced_search"),
    path("badatelske-nastroje-vysledky", views.advanced_search_results, name="advanced_search_results"),
    # static pages
    path("o-projektu", views.about_project, name="about_project"),
    path("pro-skoly", views.for_schools, name="for_schools"),
    path("osobni-udaje", views.personal_data, name="personal_data"),
    path("editori", views.editors, name="editors"),
    path("edicni-poznamka", views.editorial_note, name="editorial_note"),
    path('robots.txt', views.robots, name='robots'),
]