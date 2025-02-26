from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

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
    # rejstrik
    path("rejstrik/mist", views.geo_rejstrik, name="geo_rejstrik"),
    path("rejstrik/<int:id>", views.entity_detail, name="entity_detail"),
    # search
    path("hledani", views.search, name="search"),
    path('cancel-search/', views.cancel_search, name='cancel_search'),
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

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)