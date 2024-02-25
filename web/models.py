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
    sex = models.CharField(
        max_length=1,
        choices=SEX_CHOICES,
        default=("M", "Male")
    )
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
    title = models.CharField(max_length=255)

    authors = models.ManyToManyField(Person, through='Authorship', related_name='books')

    def __str__(self):
        return self.title
    

class Authorship(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="authorships")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="authorships")
    author_order = models.PositiveIntegerField()

    class Meta:
        ordering = ['author_order']
        unique_together = (('person', 'book', 'author_order'),)  # Ensures uniqueness

    def __str__(self):
        return f"{self.person} - {self.book}"