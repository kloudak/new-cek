from datetime import datetime
import re

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
    no_xml_string = re.sub(html_tag_pattern, ' ', xml_string).replace('  ', ' ')
    
    return no_xml_string
