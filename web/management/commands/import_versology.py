import csv, json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import Poem, Book, PoemInCCV
from web.utils import xsampa_to_czech_word

metre = {
    "A" : "Amfibrach",
    "D" : "Daktyl",
    "J" : "Jamb",
    "N" : "Neurčeno",
    "T" : "Trochej",
    "X" : "Daktylotrochej",
    "Y" : "Daktylotrochej s předrážkou",
    "H" : "Hexametr"
}

clause = {
    "a" : "akatelaktická",
    "f" : "ženská",
    "m" : "mužská",
    "n" : "neurčená"
}

def process_strophe(s, stats):
    html = "<strofa>\n"
    stats['n_strophe'] += 1
    for v in s:
        stats['n_verse'] += 1
        pattern = v["metre"][0]["pattern"]
        stress = v["stress"]
        m_rhyme = v["rhyme"]
        m_type = v["metre"][0]['type']
        if m_type == 'hexameter':
            m_type = "H"
        if not m_type in stats['metre']:
            stats['metre'][m_type] = 0
        stats['metre'][m_type] += 1
        m_clause = v["metre"][0]['clause']
        m_foot = v["metre"][0]['foot']
        metre_info = f"({m_type}{m_foot}{m_clause})"
        verse_title = f"metrum: {metre.get(m_type, 'Neurčeno')} ({clause.get(m_clause, 'neurčená')} klauzule"
        if m_foot != '' and int(m_foot) >= 5:
            verse_title += f", {m_foot} stop"
        elif m_foot != '' and  int(m_foot) > 0:
            verse_title += f", {m_foot} stopy"
        verse_title += ")<br><br>"
        verse_title += f"metrický&nbsp;vzorec:&nbsp;{pattern}<br>"
        html += f"\t<v m-rhyme=\"{m_rhyme}\" m-type=\"{m_type}\" m-foot=\"{m_foot}\" m-clause=\"{m_clause}\"\">"
        html += f"<span class=\"v-text\" data-bs-html=\"true\" title=\"{verse_title}\">"
        verse = ""
        prepend = ""
        syl_idx = 0
        for w in v["words"]:
            if len(w['token']) == 1 and w['token'] not in 'aeiouáéíóůú':
                prepend = f"{w['token']} "
                continue
            syl_length = 0
            syls = []
            if len(w["pyphen_syllables"]) < len(w["sampa_syllables"]):
                for syl in w["sampa_syllables"]:
                    syl = xsampa_to_czech_word(syl, w['token'])
                    syls.append(syl)
                    syl_length += len(syl)
            else:
                for syl in w["pyphen_syllables"]:
                    syls.append(syl)
                    syl_length += len(syl)
            position = 0
            for idx, syl in enumerate(syls):
                if idx < len(syls) - 1:
                    wf = w["token"][position:(position + len(syl))]
                else: 
                    wf = w["token"][position:]
                if idx == 0 and prepend != "":
                    wf = prepend + wf
                position += len(syl)
                if len(pattern) > syl_idx:
                    if syl_idx < len(stress) and stress[syl_idx] == "1":
                        p = f"{pattern[syl_idx]} stress"
                    else:
                        p = f"{pattern[syl_idx]}"
                    syl_idx += 1
                else:
                    p = "U"
                verse += f'<syl class="{p}">{wf}</syl>'
            verse += ' '
            prepend = ""
        html += f"{verse[:-1]}</span><span class=\"metre-info\">{metre_info}</span></v>\n"
    html += "</strofa>\n\n"
    return html, stats

def read_poem_in_ccv(book_id, poem_id, stats):
    versology_html = ""
    book_id = str(book_id)
    book_id = "0000"[:-len(book_id)] + book_id
    file_path = f"./web/data/ccv_syllables/{book_id}.json"
    with open(file_path, newline='', encoding='utf-8') as jsonfile:
        content = json.load(jsonfile)
    poem = None
    for p in content:
        if p['poem_id'] == poem_id:
            poem = p
    if poem is None:
        return None
    for s in poem["body"]:
        html, stats = process_strophe(s, stats)
        versology_html += html
    return versology_html, stats

class Command(BaseCommand):
    help = 'Goes through all poems in the database and upsert the versology fields.'
    
    def handle(self, *args, **kwargs):
        prev_book = 0
        for poem in Poem.objects.all().order_by('id'):
            book_id = poem.book.id
            if book_id != prev_book:
                self.stdout.write(self.style.SUCCESS(f'Processing book id = {book_id}.'))
            prev_book = book_id
            ccv_poems = poem.poems_in_ccv.all()
            content = ""
            stats = {
                "n_strophe" : 0,
                "n_verse" : 0,
                "metre" : {}
            }
            for ccv_poem in ccv_poems:
                versology_html, stats = read_poem_in_ccv(book_id, ccv_poem.ccv_id, stats)
                content += versology_html
            poem.versology_text = content
            poem.versology_stats = json.dumps(stats)
            poem.save()
            