# Generated by Django 5.0.2 on 2024-09-28 08:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0021_poem_similar_poems"),
    ]

    operations = [
        migrations.RenameField(
            model_name="person",
            old_name="description",
            new_name="side_note",
        ),
        migrations.AddField(
            model_name="book",
            name="side_note",
            field=models.TextField(blank=True, null=True),
        ),
    ]
