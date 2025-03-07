from datetime import datetime
import re, os, requests

def years_difference(date1, date2):
    """
    Compute the difference in years between two dates.
    
    Parameters:
    - date1, date2: dates of datetime type, assuming date2 > date1
    
    Returns:
    - int: The difference in years between the two dates.
    """
    # Compute the difference in years
    difference = date2.year - date1.year
    
    # Adjust the difference if date2 is before the date1's anniversary
    if date2.month < date1.month or (date2.month == date1.month and date2.day < date1.day):
        difference -= 1
    
    return difference


def remove_html_tags(xml_string):
    """
    Removes all HTML tags from the given XML string.

    Parameters:
    - xml_string: The XML content as a string.

    Returns:
    - The string with all HTML tags removed.
    """
    # Define a regular expression pattern for HTML tags
    html_tag_pattern = re.compile(r'<.*?>')
    
    # Replace HTML tags with an empty string
    no_xml_string = re.sub(html_tag_pattern, '', xml_string).replace('  ', ' ')
    
    return no_xml_string

def compare_lists(xml_list, db_list):
    # Check if lists are exactly the same
    if xml_list == db_list:
        return True, ""
    
    message_parts = []
    
    # Check for missing elements in db_list
    missing_in_db_list = [item for item in xml_list if item not in db_list]
    if missing_in_db_list:
        missing_str = ", ".join(str(item) for item in missing_in_db_list)
        message_parts.append(f"V databázi chybí básně s id: {missing_str}.")
    
    # Check for extra elements in db_list
    extra_in_db_list = [item for item in db_list if item not in xml_list]
    if extra_in_db_list:
        extra_str = ", ".join(str(item) for item in extra_in_db_list)
        message_parts.append(f"V databázi jsou navíc básně s id: {extra_str}.")
    
    # Check for elements in the wrong order
    if not missing_in_db_list and not extra_in_db_list:
        message_parts.append("V textu i databázi jsou stejné básně, ale v jiném pořadí.")
    elif not set(xml_list) == set(db_list):
        common_elements = set(xml_list) & set(db_list)
        common_order_issues = [item for item in xml_list if item in common_elements and xml_list.index(item) != db_list.index(item)]
        if common_order_issues:
            order_str = ", ".join(str(item) for item in common_order_issues)
            message_parts.append(f"Básně {order_str} jsou ve špatném pořadí oproti databázi.")
    
    return False, "<br />\n".join(message_parts)

def remove_elements_after(root, tag):
    """
    Remove all elements that are after tag
    The search is based on depth-first traversal.
    """
    parent_map = {c: p for p in root.iter() for c in p}
    element_found = False
    for elem in root.iter():
        # Once we encounter the given element, we set element_found to True
        if elem == tag:
            element_found = True
        # If element_found is True, and this is not the given element,
        # we remove it from its parent
        elif element_found:
            parent = parent_map[elem]
            parent.remove(elem)
    
    return root

def xsampa_to_czech_word(xsampa, orig):
    mapping = {
        # Vowels
        'r\\': 'ř',
        'l\\': 'ľ',
        'm\\': 'ĺ',
        'n\\': 'ň',
        's\\': 'ś',
        'S\\': 'š',
        'z\\': 'ź',
        'Z\\': 'ž',
        'P\\': 'ř',
        ':': '',
        '=': '',
        '"': '',
        'j\\': 'y',
        't_ś': 'č',
        't_S': 'č',
        'rJE' : 'rně',
        'jé': 'ě',
        'JE': 'ně',
        'Je': 'ě',
        'jE': 'ě',
        'o_u': 'ou',
        'a_u': 'au',
        't_s' : 'c',
        'J\\E': 'dě',
        'h\\i:': 'hý',
        'J\\' : 'ď',
        'h\\JE': 'hně',
        'h\\' : 'h',
        'x': 'ch',
        'mJE': 'mě'
    }
    # Attempt to replace based on longest matches first
    for xsampa_symbol in sorted(mapping.keys(), key=len, reverse=True):
        if xsampa_symbol == 'x':
            if 'ch' in orig:
                xsampa = xsampa.replace(xsampa_symbol, mapping[xsampa_symbol])
        elif xsampa_symbol == 'jE':
            if 'ě' in orig or 'ie' in orig:
                xsampa = xsampa.replace(xsampa_symbol, mapping[xsampa_symbol])
        elif xsampa_symbol == 'je':
            if 'ě' in orig or 'ie' in orig:
                xsampa = xsampa.replace(xsampa_symbol, mapping[xsampa_symbol])
        else:
            xsampa = xsampa.replace(xsampa_symbol, mapping[xsampa_symbol])
    return xsampa


def get_wikipedia_info(wiki_id):
    """
    Fetch Wikipedia titles, links, and summaries in Czech and English for a given Wikidata ID.

    This function performs two main tasks:
    1. Queries the Wikidata API to obtain the Wikipedia page titles (if available) for the given entity.
    2. Fetches the first paragraph summary and the Wikipedia page URL from the Wikipedia REST API.

    Parameters:
    ----------
    wiki_id : str
        The Wikidata entity ID (e.g., "Q11991502").

    Returns:
    -------
    dict
        A dictionary containing Wikipedia information in both Czech ('cs') and English ('en').
        Each language entry includes:
        - 'title': The Wikipedia page title in the respective language (if available).
        - 'url': The full URL to the Wikipedia page (if available).
        - 'summary': The first paragraph of the Wikipedia page (if available).

        Example output:
        {
            "wiki_id": "Q11991502",
            "cs": {
                "title": "Nějaké město",
                "url": "https://cs.wikipedia.org/wiki/N%C4%9Bjak%C3%A9_m%C4%9Bsto",
                "summary": "Nějaké město je významné místo v České republice..."
            },
            "en": {
                "title": "Some City",
                "url": "https://en.wikipedia.org/wiki/Some_City",
                "summary": "Some City is a historic place located in..."
            }
        }

    Notes:
    ------
    - If a Wikipedia page is not available for a given language, the corresponding fields ('title', 'url', 'summary') will be `None`.
    - The Wikipedia REST API is used to retrieve summaries, which may vary in length.
    - No caching is implemented, so repeated calls may slow performance.

    """
    wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={wiki_id}&props=sitelinks&format=json"

    # Fetch Wikipedia page titles from Wikidata
    response = requests.get(wikidata_url)
    data = response.json()

    cs_title = data["entities"].get(wiki_id, {}).get("sitelinks", {}).get("cswiki", {}).get("title")
    en_title = data["entities"].get(wiki_id, {}).get("sitelinks", {}).get("enwiki", {}).get("title")

    result = {
        "wiki_id": wiki_id,
        "cs": {"title": cs_title, "url": None, "summary": None},
        "en": {"title": en_title, "url": None, "summary": None}
    }

    def get_wikipedia_summary(lang, title):
        """
        Retrieve the first paragraph summary and URL of a Wikipedia page.

        Parameters:
        ----------
        lang : str
            The language code for Wikipedia (e.g., 'cs' for Czech, 'en' for English).
        title : str
            The Wikipedia page title.

        Returns:
        -------
        dict or None
            Dictionary with 'url' and 'summary' keys if successful, otherwise None.
        """
        if not title:
            return None
        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
        res = requests.get(summary_url)
        if res.status_code == 200:
            summary_data = res.json()
            return {
                "url": summary_data.get("content_urls", {}).get("desktop", {}).get("page"),
                "summary": summary_data.get("extract")
            }
        return None

    # Get Wikipedia summaries for Czech and English
    if cs_title:
        cs_data = get_wikipedia_summary("cs", cs_title)
        if cs_data:
            result["cs"]["url"] = cs_data["url"]
            result["cs"]["summary"] = cs_data["summary"]

    if en_title:
        en_data = get_wikipedia_summary("en", en_title)
        if en_data:
            result["en"]["url"] = en_data["url"]
            result["en"]["summary"] = en_data["summary"]

    return result
