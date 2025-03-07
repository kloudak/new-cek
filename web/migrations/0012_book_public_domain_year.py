# Generated by Django 5.0.2 on 2024-04-04 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0011_poemoftheday"),
    ]

    operations = [
        migrations.AddField(
            model_name="book",
            name="public_domain_year",
            field=models.IntegerField(
                blank=True,
                help_text="Year when the book enters the public domain, based on the author's death year + 70 years.",
                null=True,
                verbose_name="Public Domain Start Year",
            ),
        ),
    ]
