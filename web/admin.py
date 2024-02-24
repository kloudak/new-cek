from django.contrib import admin

from .models import Person

class PersonAdmin(admin.ModelAdmin):
    list_display = ('surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')
    search_fields = ('surname', 'firstname', 'date_of_birth', 'date_of_death')
    ordering = ('surname', 'firstname', 'date_of_birth', 'date_of_death', 'sex', 'pseudonym_for')

admin.site.register(Person, PersonAdmin)
