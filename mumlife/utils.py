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
from dateutil.relativedelta import relativedelta

logger = logging.getLogger('mumlife.utils')

REGEX_TAGS = re.compile(r'(#[_\w-]+)')
REGEX_FLAGS = re.compile(r'(@[_\w-]+)')

# URLs
# @see https://github.com/ianozsvald/twitter-text-python
UTF_CHARS = ur'a-z0-9_\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff'
PRE_CHARS = ur'(?:[^/"\':!=]|^|\:)'
DOMAIN_CHARS = ur'([\.-]|[^\s_\!\.\/])+\.[a-z]{2,}(?::[0-9]+)?'
PATH_CHARS = ur'(?:[\.,]?[%s!\*\'\(\);:=\+\$/%s#\[\]\-_,~@])' % (UTF_CHARS, '%')
QUERY_CHARS = ur'[a-z0-9!\*\'\(\);:&=\+\$/%#\[\]\-_\.,~]'
# Valid end-of-path chracters (so /foo. does not gobble the period).
# 1. Allow ) for Wikipedia URLs.
# 2. Allow =&# for empty URL parameters and other URL-join artifacts
PATH_ENDING_CHARS = r'[%s\)=#/]' % UTF_CHARS
QUERY_ENDING_CHARS = '[a-z0-9_&=#]'
REGEX_URL = re.compile('((%s)((https?://|www\\.)(%s)(\/(%s*%s)?)?(\?%s*%s)?))'
                       % (PRE_CHARS, DOMAIN_CHARS, PATH_CHARS,
                          PATH_ENDING_CHARS, QUERY_CHARS, QUERY_ENDING_CHARS),
                       re.IGNORECASE)

class Extractor(object):

    def __init__(self, string):
        self.string = string

    def parse(self, with_links=True):
        if not with_links:
            # replace hashtags and flags only, with spans
            s = REGEX_TAGS.sub(self.replace_with_spans, self.string)
            s = REGEX_FLAGS.sub(self.replace_with_spans, s)
            return s
        # parse hashtags, flags and links
        s = REGEX_TAGS.sub(self.replace_with_hash, self.string)
        s = REGEX_FLAGS.sub(self.replace_with_flag, s)
        s = REGEX_URL.sub(self.replace_with_link, s)
        return s

    def replace_with_spans(self, matchobj):
        hashtag = matchobj.group(0)
        return '<span>{}</span>'.format(hashtag)

    def replace_with_hash(self, matchobj):
        hashtag = matchobj.group(0)
        return '<a href="/local/%23{}">{}</a>'.format(hashtag[1:], hashtag)

    def replace_with_flag(self, matchobj):
        flagtag = matchobj.group(0)
        if flagtag not in ('local', 'global', 'friends'):
            return flagtag
        return '<a href="/local/@{}">{}</a>'.format(flagtag[1:], flagtag)

    def replace_with_link(self, matchobj):
        link = matchobj.group(0)
        return '<a href="{}" target="_blank">{}</a>'.format(link, link)

    def extract_tags(self):
        """
        Extract hashtags from a string.
        hashtags are returned as dictionaries, whose keys are the hastags values
        without the leading character #.

        """
        tags = {}
        for match in REGEX_TAGS.findall(self.string):
            tags[re.sub(r'#', '', match)] = match
        return tags

    def extract_flags(self):
        """
        Extract flags from a string.
        flags are returned as a 1-dimension list.

        """
        allowed = ['@local', '@global', '@friends', '@private']
        matches = REGEX_FLAGS.findall(self.string)
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
    if type(born) is str:
        # Attempt to convert string to date
        try:
            born = datetime.datetime.strptime(born, '%Y-%m-%d').date()
        except:
            raise
    today = datetime.date.today()
    age = relativedelta(today, born)
    # For babies and toddlers (i.e. age <= 24 months),
    # we display the number of months, or weeks for small babies
    months = (12 * age.years) + age.months + (.01 * age.days)
    if months < 1:
        weeks = int(age.days / 7)
        return '{} week{}'.format(weeks, 's' if weeks > 1 else '')
    if months <= 24:
        months = int(months)
        return '{} month{}'.format(months, 's' if months > 1 else '')
    else:
        return '{} years'.format(age.years)


def get_age_bracket(born):
    if not born:
        return 'N/A'
    if type(born) is str:
        # Attempt to convert string to date
        try:
            born = datetime.datetime.strptime(born, '%Y-%m-%d').date()
        except:
            raise
    today = datetime.date.today()
    age = relativedelta(today, born).years
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
