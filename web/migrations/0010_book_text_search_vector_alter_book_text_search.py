# Generated by Django 5.0.2 on 2024-03-15 14:25

import django.contrib.postgres.search
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0009_poem_text_search_vector_alter_poem_text_search"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="text_search_vector",
            field=django.contrib.postgres.search.SearchVectorField(
                editable=False, null=True
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="text_search",
            field=models.TextField(editable=False, null=True),
        ),
    ]