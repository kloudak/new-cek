from datetime import datetime
import re, os

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

def log_search_to_file(query, advanced=False, log_file='web/__mylog__/search_log.txt'):
    """
    Log the search query to a specified file with a timestamp.

    This function appends the given search query along with the current
    date-time to a log file. Each log entry is written as a new line
    in the format "YYYY-MM-DD HH:MM:SS - query".

    Args:
        query (str): The search query string to be logged.
        advanced (bool): Is the seach string from advances search form?
        log_file (str): The path to the log file where the search query
                        will be appended. Defaults to 'web/__mylog__/search_log.txt'.

    Example:
        log_search_to_file("example search query")
    """
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        form = 'A' if advanced else 'F'
        log_entry = f"{current_time} - {form} - {query}\n"
        with open(log_file, 'a') as file:
            file.write(log_entry)
    except:
        return False