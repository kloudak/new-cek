from django.contrib import admin

from .models import Person, Authorship, Book

class PersonAdmin(admin.ModelAdmin):
    list_display = ('surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')
    search_fields = ('surname', 'firstname', 'date_of_birth', 'date_of_death')
    ordering = ('surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 1  # How many rows to show by default

class BookAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline,)
    list_display = ('title',)

admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)