# Generated by Django 5.0.2 on 2024-03-04 07:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0005_alter_book_edition"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
