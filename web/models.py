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
