from django.core.management.base import BaseCommand
from web.models import Book

class Command(BaseCommand):
    help = 'Goes through all books in the database and runs the save() method on each one.'

    def handle(self, *args, **kwargs):
        for book in Book.objects.all().order_by('id'):
            try:
                book.save()
            except:
                self.stdout.write(self.style.ERROR(f'Failed to update book ID={book.id})'))
