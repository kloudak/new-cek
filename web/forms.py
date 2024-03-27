from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from .models import PoemOfTheDay, Poem

class PoemOfTheDayAdminForm(forms.ModelForm):
    poem = forms.ModelChoiceField(
        queryset=Poem.objects.all(),
        widget=ForeignKeyRawIdWidget(PoemOfTheDay._meta.get_field('poem').remote_field, admin.site),
        required=False,
    )

    class Meta:
        model = PoemOfTheDay
        fields = '__all__'
