# Generated by Django 5.0.2 on 2024-07-02 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0019_book_for_schools_person_for_schools_alter_poem_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="stats",
            field=models.TextField(blank=True, null=True),
        ),
    ]
