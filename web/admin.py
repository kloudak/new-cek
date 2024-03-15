from django.contrib import admin

from .models import Person, Authorship, Book, Poem

class PersonAdmin(admin.ModelAdmin):
    list_display = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')
    list_display_links = ('surname',)
    search_fields = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death')
    ordering = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 1

class PoemInline(admin.StackedInline):
    model = Poem
    fields = ['order_in_book'] 
    extra = 0

class BookAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline, PoemInline)
    list_display = ('id','title','year','author_xml')
    list_display_links = ('id', 'title')
    search_fields = ('id','title','year','author_xml')
    ordering = ('id','title','year','author_xml')

class PoemAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'book')
    list_display_links = ('title',)
    search_fields = ('id','title', 'book')
    ordering = ('id','title')

admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Poem, PoemAdmin)