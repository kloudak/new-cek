from django.contrib import admin
from django import forms

from .models import Person, Authorship, Book, Poem, PoemOfTheDay, Clustering, Cluster, Entity, PoemAIText
from .forms import PoemOfTheDayAdminForm

class PersonAdmin(admin.ModelAdmin):
    list_display = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')
    list_display_links = ('surname',)
    search_fields = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death')
    ordering = ('id','surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')

class AuthorshipInlineForm(forms.ModelForm):
    person = forms.IntegerField(widget=forms.TextInput)

    class Meta:
        model = Authorship
        fields = '__all__'
    
    def clean_person(self):
        person_id = self.cleaned_data['person']
        try:
            person = Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            raise forms.ValidationError("Person with this ID does not exist.")
        return person

class AuthorshipInline(admin.TabularInline):
    model = Authorship
    form = AuthorshipInlineForm
    extra = 1

class PoemInline(admin.StackedInline):
    model = Poem
    fields = ['order_in_book'] 
    extra = 0

class BookAdmin(admin.ModelAdmin):
    inlines = (AuthorshipInline, PoemInline)
    list_display = ('id','title','year', 'public_domain_year','author_xml')
    list_display_links = ('id', 'title')
    search_fields = ('id','title','year', 'public_domain_year','author_xml')
    ordering = ('id','title','year', 'public_domain_year','author_xml')

class PoemAdmin(admin.ModelAdmin):
    raw_id_fields = ('next_issue_of','author')
    list_display = ('id','title', 'book')
    list_display_links = ('id','title',)
    search_fields = ('id','title')
    ordering = ('id','title')

class PoemOfTheDayAdmin(admin.ModelAdmin):
    form = PoemOfTheDayAdminForm
    list_display = ('day', 'description', 'poem')
    list_display_links = ('day',)
    search_fields = ('day', 'description', 'poem')
    ordering = ('day',)

class ClusteringAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ClusterAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'clustering', 'description', 'number_of_documents')
    list_display_links = ('id','name', 'description')
    search_fields = ('name', 'clustering__name')
    list_filter = ('clustering__name',)

class EntityAdmin(admin.ModelAdmin):
    list_display = ('lemma', 'type', 'wiki_id', 'to_index')
    list_filter = ('type', 'to_index')
    search_fields = ('lemma', 'wiki_id')
    ordering = ('type', 'lemma')
    list_editable = ('to_index',)
    fieldsets = (
        (None, {'fields': ('lemma', 'type', 'wiki_id', 'to_index')}),
    )

class PoemAITextAdmin(admin.ModelAdmin):
    list_display = ('poem_id', 'poem',)  
    search_fields = ('poem__title',)
    ordering = ('poem',)
    list_filter = ('poem__book',)
    readonly_fields = ('poem',)
    fieldsets = (
        (None, {'fields': ('poem', 'text')}),
    )

admin.site.register(Person, PersonAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Poem, PoemAdmin)
admin.site.register(PoemOfTheDay, PoemOfTheDayAdmin)
admin.site.register(Clustering, ClusteringAdmin)
admin.site.register(Cluster, ClusterAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(PoemAIText, PoemAITextAdmin)