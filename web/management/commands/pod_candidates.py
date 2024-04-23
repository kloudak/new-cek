from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_date
from datetime import timedelta, date
from web.models import PoemOfTheDay, Person

def add_years(orig_date, years):
    try:
        return orig_date.replace(year=orig_date.year + years)
    except ValueError:
        if orig_date.month == 2 and orig_date.day == 29:
            return orig_date.replace(year=orig_date.year + years, month=2, day=28)
        raise

class Command(BaseCommand):
    help = 'Create PoemOfTheDay instances for a range of dates'

    def add_arguments(self, parser):
        parser.add_argument('--from', dest='from_date', type=str, help='Start date (YYYY-MM-DD)')
        parser.add_argument('--to', dest='to_date', type=str, help='End date (YYYY-MM-DD)')

    def handle(self, *args, **options):
        from_date = options['from_date']
        to_date = options['to_date']

        try:
            from_date = parse_date(from_date)
            to_date = parse_date(to_date)
            if not from_date or not to_date:
                raise ValueError
        except ValueError:
            raise CommandError(f'Invalid date format. Use YYYY-MM-DD. {from_date} - {to_date}')
        
         # Ensure the from_date is before the to_date
        if from_date > to_date:
            raise CommandError('"From" date must be before "to" date.')

        current_date = from_date
        html_output = ""
        while current_date <= to_date:
            pod = PoemOfTheDay.objects.filter(day=current_date).first()
            html_part = f"""<h4>
                            výročí pro den: 
                            <a target="blank" href=\"https://new-cek.pythonanywhere.com/admin/web/poemoftheday/{pod.id}/change/\">
                                {current_date}
                            </a>
                            </h4>"""
            persons_b = []
            persons_d = []
            for addyears in range(10,290,10):
                thedate = add_years(current_date, -addyears)
                persons_b += list(Person.objects.filter(date_of_birth=thedate).all())
                persons_d += list(Person.objects.filter(date_of_death=thedate).all())
            if len(persons_b) + len(persons_d) > 0:
                html_part += "\n<ul>"
                for p in persons_b:
                    html_part += f"""
                        <li>
                        {current_date.year - p.date_of_birth.year} let od narození autora
                        <a target="blank" href="https://new-cek.pythonanywhere.com/autori/{p.id}">{p}</a>.
                        </a>
                    """
                for p in persons_d:
                    html_part += f"""
                        <li>
                        {current_date.year - p.date_of_death.year} let od smrti autora
                        <a href="https://new-cek.pythonanywhere.com/autori/{p.id}">{p}</a>.
                        </a>
                    """
                html_part += "\n</ul>"
                html_output += html_part
            current_date += timedelta(days=1)
        
        print(html_output)