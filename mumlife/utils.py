# mumlife/utils.py
"""
Utility module.

"""
import logging
import datetime
import json
import math
import re
import requests
from django.conf import settings

logger = logging.getLogger('mumlife.utils')


class Extractor(object):
    regex_tags = re.compile(r'(#[_\w-]+)')
    regex_flags = re.compile(r'(@[_\w-]+)')

    def __init__(self, string):
        self.string = string

    def parse(self, with_links=True):
        if not with_links:
            # Replace with span
            return self.regex_tags.sub(self.replace_with_spans, self.string)
        return self.regex_tags.sub(self.replace_with_links, self.string)

    def replace_with_spans(self, matchobj):
        hashtag = matchobj.group(0)
        return '<span>{}</span>'.format(hashtag)

    def replace_with_links(self, matchobj):
        hashtag = matchobj.group(0)
        return '<a href="{}local/%23{}">{}</a>'.format(settings.SITE_URL, hashtag[1:], hashtag)

    def extract_tags(self):
        """
        Extract hashtags from a string.
        hashtags are returned as dictionaries, whose keys are the hastags values
        without the leading character #.

        """
        tags = {}
        for match in self.regex_tags.findall(self.string):
            tags[re.sub(r'#', '', match)] = match
        return tags

    def extract_flags(self):
        """
        Extract flags from a string.
        flags are returned as a 1-dimension list.

        """
        allowed = ['@local', '@global', '@friends', '@private']
        matches = self.regex_flags.findall(self.string)
        return filter(lambda x: x in matches, allowed)

    def extract_postcode(self):
        """
        Extract UK postcode.

        """
        outcode_pattern = '[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])'
        incode_pattern = '[0-9][ABD-HJLNP-UW-Z]{2}'
        postcode_re = re.compile(r'(GIR 0AA|%s %s)' % (outcode_pattern, incode_pattern))
        space_re = re.compile(r' *(%s)$' % incode_pattern)
        location = space_re.sub(r' \1', self.string.upper().strip())
        postcode = postcode_re.search(location)
        if postcode is not None:
            return postcode.group(1)
        return None

def get_age(born):
    if not born:
        return 'N/A'
    today = datetime.date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError: # raised when birth date is February 29 and the current year is not a leap year
        birthday = born.replace(year=today.year, day=born.day-1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


def get_age_bracket(dob):
    if type(dob) is str:
        # Attempt to convert string to date
        try:
            dob = datetime.datetime.strptime(dob, '%d/%m/%Y').date()
        except:
            raise
    age = get_age(dob)
    if age <= 0:
        return 'Baby'
    elif age <= 2:
        return 'Toddler'
    elif age <= 12:
        return 'Child'
    elif age <= 17:
        return 'Teenager'
    else:
        return 'Adult'
    

BING_MAPS_KEY = 'AmXCuMvaJGPW0JXSQmcO4e5hKauvjs_TztK0DGcinHK6mFaVAq5lm3OzHkAPnpyE'
BING_MAPS_LOCATION_URL = 'http://dev.virtualearth.net/REST/v1/Locations'

def get_postcode_point(postcode):
    """
    Use the Bing Maps REST API to get the location point for a postcode.
    http(s)://msdn.microsoft.com/en-us/library/ff701714.aspx

    Return floating point minutes tuple: (latitude, longitude)

    """
    url = BING_MAPS_LOCATION_URL
    params = {
        'postalCode': postcode,
        'key': BING_MAPS_KEY
    }
    response = requests.get(url, params=params)
    if response.text:
        try:
            data = json.loads(response.text)
        except Exception:
            raise
        else:
            if data["statusCode"] != 200:
                raise Exception('API Error: {}'.format(data["statusDescription"]))
            try:
                coordinates = data["resourceSets"][0]["resources"][0]["point"]["coordinates"]
            except (IndexError, KeyError):
                raise Exception('API Error: {}'.format('Invalid postcode'))
            else:
                return (coordinates[0], coordinates[1])
    return (0, 0)


def get_postcodes_distance(postcode_from, postcode_to):
    """
    Calculates the distance between 2 postcodes, 
    using the Haversine formula.

    Returns a tuple with kilometers and miles values.
    1Km is equivalent to 0.6214 miles.

    """
    point_from = get_postcode_point(postcode_from)
    point_to = get_postcode_point(postcode_to)
    return get_distance(point_from[0], point_from[1], point_to[0], point_to[1])


def get_distance(latitude_from, longitude_from, latitude_to, longitude_to):
    R = 6371;
    dLon = math.radians(longitude_to - longitude_from)
    dLat = math.radians(latitude_to - latitude_from)
    lat1 = math.radians(latitude_from);
    lat2 = math.radians(latitude_to);
    a = math.sin(dLat/2) * math.sin(dLat/2) \
      + math.sin(dLon/2) * math.sin(dLon/2) \
      * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c; # KM
    miles = distance * 0.6214
    return (distance, miles)
