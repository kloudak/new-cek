from django.contrib import admin

from .models import Person, Authorship, Book

class PersonAdmin(admin.ModelAdmin):
    list_display = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')
    list_display_links = ('surname',)
    search_fields = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death')
    ordering = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 1  # How many rows to show by default

class BookAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline,)
    list_display = ('id','title','year','author_xml')
    list_display_links = ('title',)
    search_fields = ('id','title','year','author_xml')
    ordering = ('id','title','year','author_xml')

admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)