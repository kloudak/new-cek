# Generated by Django 5.0.2 on 2024-07-08 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0020_person_stats"),
    ]

    operations = [
        migrations.AddField(
            model_name="poem",
            name="similar_poems",
            field=models.TextField(blank=True, null=True),
        ),
    ]
