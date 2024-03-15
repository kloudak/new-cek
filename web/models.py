from django.db import models


class Person(models.Model):
    SEX_CHOICES = (
        ("M", "Male"),
        ("F", "Female"),
    )

    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=100, null=True, blank=True)
    place_of_death = models.CharField(max_length=100, null=True, blank=True)
    place_of_birth_original_name = models.CharField(
        max_length=100, null=True, blank=True
    )
    place_of_death_original_name = models.CharField(
        max_length=100, null=True, blank=True
    )
    remark = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default=("M", "Male"))
    pseudonym_for = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pseudonyms",
    )

    def __str__(self):
        return f"{self.firstname} {self.surname}"


class Book(models.Model):
    title = models.TextField(null=True)  # 'titul'
    subtitle = models.TextField(blank=True, null=True)  # 'podtitul'
    place_of_publication = models.CharField(
        max_length=255, blank=True, null=True
    )  # 'misto'
    publisher = models.TextField(blank=True, null=True)  # 'vydavatel'
    year = models.IntegerField(blank=True, null=True)  # 'rok' as YYYY
    edition = models.TextField(blank=True, null=True)  # 'vydani'
    pages = models.CharField(max_length=255, blank=True, null=True)  # 'stran'
    dedication = models.TextField(blank=True, null=True)  # 'venovani'
    motto = models.TextField(blank=True, null=True)  # 'moto'
    author_of_motto = models.TextField(blank=True, null=True)  # 'autormota'
    format = models.CharField(max_length=255, blank=True, null=True)  # 'format'
    description = models.TextField(blank=True, null=True)  # 'popis'
    source_signature = models.CharField(
        max_length=255, blank=True, null=True
    )  # 'zdroj-signatura'
    editorial_note = models.TextField(blank=True, null=True)  # 'edicnipoznamka'
    author_xml = models.TextField(blank=True, null=True)  # 'autor' in the source XML
    text = models.TextField(null=True)  # 'text'
    text_search = models.TextField(
        null=True, editable=False, db_index=True
    )  # text without tags
    content = models.TextField(null=True, editable=False)  # content of the book

    authors = models.ManyToManyField(Person, through="Authorship", related_name="books")

    def __str__(self):
        return self.title


class Authorship(models.Model):
    person = models.ForeignKey(
        Person, on_delete=models.PROTECT, related_name="authorships"
    )
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="authorships")
    author_order = models.PositiveIntegerField()

    class Meta:
        ordering = ["author_order"]
        unique_together = (("person", "book", "author_order"),)  # Ensures uniqueness

    def __str__(self):
        return f"{self.person} - {self.book}"


class Poem(models.Model):
    title = models.TextField(null=True)  # 'titul'
    original_id = models.PositiveIntegerField(null=True)  # id in the original XML
    order_in_book = models.PositiveIntegerField(null=False, blank=False)  # order in the book
    book = models.ForeignKey(
        Book, on_delete=models.PROTECT, related_name="poems"
    )  # the book the poem is part of
    text = models.TextField(null=True)  # 'text'
    text_search = models.TextField(
        null=True, editable=False, db_index=True
    )  # 'text without tags'
    author = models.ForeignKey(
        Person, on_delete=models.PROTECT, null=True, blank=True
    )  # author is taken from the book if this is null and the book has axactly one author

    def __str__(self):
        return self.title if self.title is not None else f"Untitled Poem #{self.id}"
