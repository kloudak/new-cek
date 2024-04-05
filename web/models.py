from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.postgres.search import SearchVectorField, SearchVector
import xml.etree.ElementTree as ET
from .utils import remove_html_tags, compare_lists, remove_elements_after


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
    complete_text = None

    title = models.TextField(null=True)  # 'titul'
    subtitle = models.TextField(blank=True, null=True)  # 'podtitul'
    place_of_publication = models.CharField(
        max_length=255, blank=True, null=True
    )  # 'misto'
    publisher = models.TextField(blank=True, null=True)  # 'vydavatel'
    year = models.IntegerField(blank=True, null=True)  # 'rok' as YYYY
    public_domain_year = models.IntegerField(
        verbose_name="Public Domain Start Year",
        help_text="Year when the book enters the public domain, based on the author's death year + 71 years.",
        null=True,
        blank=True
    )
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
    text_search = models.TextField(null=True, editable=False)  # 'text'
    text_search_vector = SearchVectorField(
        null=True, editable=False
    )  # 'text without tags'
    content = models.TextField(null=True, editable=False)  # content of the book

    authors = models.ManyToManyField(Person, through="Authorship", related_name="books")

    def __str__(self):
        return remove_html_tags(self.title)
    
    def clean(self):
        super().clean()

        if self.public_domain_year:
            year_str = str(self.public_domain_year)
            if len(year_str) != 4 or not year_str.isdigit():
                raise ValidationError({
                    'public_domain_year': "Year must be in YYYY format."
                })

    def save(self, *args, import_xml=False, **kwargs):
       
        if not import_xml:
            db_ids = list(self.poems.order_by('order_in_book').values_list('id', flat=True))
            xml_ids = self._get_cekid_values()
            # print(f"poems: \n {db_ids} \n {xml_ids}")
            is_ok, message = compare_lists(xml_ids, db_ids)
            if not is_ok:
                raise ValidationError(message)
        self._content_string()
        # Modify the text_search field before saving
        # remove HTML tags from self.text and assign it to self.text_search
        if self.text is not None:
            self.text_search = remove_html_tags(self.text)
        # Call the superclass's save method to handle the actual saving
        super().save(*args, **kwargs)
        Poem.objects.filter(pk=self.pk).update(text_search_vector =SearchVector('text_search'))

    def set_complete_text(self):
        texts = {p.id : p.text for p in self.poems.order_by('order_in_book')}
        root = ET.fromstring(f"<div class=\"book-text\">\n{self.text}\n</div>")
        # Iterate through all <basen> elements
        for basen in root.findall('.//basen'):
            if not 'cekid' in basen.attrib:
                continue
            cekid = int(basen.get('cekid'))
            if cekid > 0:
                poem_url = reverse('poem_in_book', kwargs={'id': cekid})
                a_element = ET.Element('a', href=poem_url)
                icon_element = ET.Element('i')
                icon_element.set('class', 'bi bi-arrow-right-square')
                icon_element.text = " "
                a_element.text=" "
                a_element.append(icon_element)
                a_element.set('class', 'poem-link')
                basen.append(a_element)
            if cekid in texts:
                basen_content = ET.fromstring(f"\n<div class=\"poem-text\">{texts[cekid]}\n</div>\n")
                basen.append(basen_content)
            for nadpis in root.findall(".//nadpis[@prazdny='ano']"):
                parent = nadpis.find("..")
                if parent is not None:
                    parent.remove(nadpis)

        order = 0
        for elem in root.findall(".//*[@data-to-content='1']"):
            elem.set('id', f'polozka-obsahu-{order}')
            order += 1
        self.complete_text = ET.tostring(root, encoding='unicode', method='xml')
        self.complete_text = self.complete_text.replace("<nbsp />","&nbsp;").\
                                replace("<tab />", "&nbsp;&nbsp;&nbsp;&nbsp;")
        

    def _get_cekid_values(self):
        # Parse the XML string
        root = ET.fromstring(f"<bookroot>{self.text}</bookroot>")
        # Initialize an empty list to store cekid values
        cekid_values = []
        # Iterate through all 'basen' tags and extract the 'cekid' attribute
        for basen in root.findall('.//basen'):
            cekid = basen.attrib.get('cekid')
            if cekid is not None:
                cekid_values.append(int(cekid))
        
        return cekid_values
    
    def _content_string(self):
        content = self._extract_content()
        self.content = "<ul id=\"book-content\">\n"
        for idx, ci in enumerate(content):
            if len(ci['title']) > 0:
                title = remove_html_tags(ci['title']).strip()
            else:
                if ci['tag_name'] == 'basen':
                    if ci['cekid']:
                        ptitle = self.poems.get(id=ci['cekid']).title
                        if isinstance(ptitle, str):
                            title = remove_html_tags(ptitle).strip()
                        else:
                            title = f"<i>báseň bez názvu</i>"    
                    else:
                        title = f"<i>báseň bez názvu</i>"
                elif ci['tag_name'] == 'oddil':
                    title = f"<i>oddíl bez názvu</i>"
                else:
                    title = f"<i>položka bez názvu</i>"
            self.content += f"""
            <li data-level=\"{ci['level']}\">
                <a href=\"#polozka-obsahu-{idx}\">{title}</a>
            </li>"""
        self.content += "</ul>\n"
    
    def _extract_content(self):
        # Parse the XML string into an ElementTree object
        root = ET.fromstring(f"<bookroot>{self.text}</bookroot>")
        
        # Initialize an empty list to store dictionaries of tag info
        tag_info_list = []
        
        # Initialize a counter to track the order of elements
        order_counter = 0
        
        # Define a recursive function to traverse the tree
        def traverse(element, level):
            nonlocal order_counter
            if element.get('data-to-content') == "1":
                cekid = element.attrib['cekid'] if 'cekid' in element.attrib else None
                order_counter += 1
                # Initialize title as an empty string
                title = ""
                # Check if the first child is a <nadpis> tag and capture its content
                nadpis = next((child for child in element if child.tag == 'nadpis'), None)
                if nadpis is not None:
                    # Using ET.tostring to include tags within the content and decode it
                    title = ET.tostring(nadpis, encoding='unicode', method='xml')
                
                tag_info_list.append({
                    'tag_name': element.tag,
                    'order': order_counter,
                    'level': level,
                    'title': title,
                    "cekid" : cekid
                })
            
            for child in element:
                traverse(child, level + 1)
            
        # Start traversing from the root
        traverse(root, 0)
        
        return tag_info_list
        

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
    html_text = None

    title = models.TextField(null=True)  # 'titul'
    original_id = models.PositiveIntegerField(null=True)  # id in the original XML
    order_in_book = models.PositiveIntegerField(null=False, blank=False)  # order in the book
    book = models.ForeignKey(
        Book, on_delete=models.PROTECT, related_name="poems"
    )  # the book the poem is part of
    text = models.TextField(null=True)  # 'text'
    text_search = models.TextField(null=True, editable=False)  # 'text'
    text_search_vector = SearchVectorField(
        null=True, editable=False
    )  # 'text without tags'
    author = models.ForeignKey(
        Person, on_delete=models.PROTECT, null=True, blank=True
    )  # author is taken from the book if this is null and the book has axactly one author

    def __str__(self):
        return remove_html_tags(self.title) if self.title is not None else f"Báseň bez názvu #{self.id}"

    def save(self, *args, **kwargs):
        # Modify the text_search field before saving
        # remove HTML tags from self.text and assign it to self.text_search
        if self.text is not None:
            self.text_search = remove_html_tags(self.text)
        # Call the superclass's save method to handle the actual saving
        super().save(*args, **kwargs)
        Poem.objects.filter(pk=self.pk).update(text_search_vector =SearchVector('text_search'))

    def set_html_text(self):
        root = ET.fromstring(f"<div class=\"poem-text\">\n{self.text}\n</div>")
        for nadpis in root.findall(".//nadpis[@prazdny='ano']"):
            parent = nadpis.find("..")
            if parent is not None:
                parent.remove(nadpis)

        self.html_text = ET.tostring(root, encoding='unicode', method='xml')
        self.html_text = self.html_text.replace("<nbsp />","&nbsp;").\
                                replace("<tab />", "&nbsp;&nbsp;&nbsp;&nbsp;")
        

class PoemOfTheDay(models.Model):
    html_text = ""

    day = models.DateField(blank=False)
    poem = models.ForeignKey(Poem, on_delete=models.SET_NULL, related_name="day", null=True)
    description= models.TextField(blank=True, null=True)

    def __str__(self):
        return self.day.strftime('%Y-%m-%d')

    def set_poem_text(self):
        """
        Truncates the poem text associated with the PoemOfTheDay instance to a maximum of max_n_strophes strophes 
        or max_n_verses verses. If the original poem exceeds these limits, it is truncated, 
        and an ellipsis (...) is appended to indicate the poem text is incomplete.

        All tags after the last strophe/verse is truncated.

        Attributes modified:
        - self.html_text
        """

        # settings
        max_n_strophes = 3
        max_n_verses = 10

        root = ET.fromstring(f"<div class=\"poem-text\">\n{self.poem.text}\n</div>")
        sc = 1
        vc = 1
        incomplete = False
        last_strofa = None
        last_verse = None
        # removing strofa and v tags
        for strofa in root.findall(".//strofa"):
            if sc > max_n_strophes or vc > max_n_verses:
                root.remove(strofa)
                incomplete = True
                continue
            else:
                last_strofa = strofa
            for verse in strofa.findall(".//v"):
                if vc > max_n_verses:
                    strofa.remove(verse)
                    incomplete = True
                else:
                    last_verse = verse
                vc += 1
            sc += 1
        # removing everithing after the last tag
        last_element = last_verse if last_verse is not None else last_strofa
        root = remove_elements_after(root, last_element)

        # adding span tag <span>...</span> to indicate incomplete text
        if incomplete:
            span_tag = ET.Element('span')
            span_tag.text = "..."
            span_tag.set('class', 'incomplete-poem')
            root.append(span_tag)

        # saving modified XML to a string
        self.html_text = ET.tostring(root, encoding='unicode', method='xml')
        self.html_text = self.html_text.replace("<nbsp />","&nbsp;").\
                                replace("<tab />", "&nbsp;&nbsp;&nbsp;&nbsp;").\
                                replace("<br />", "")