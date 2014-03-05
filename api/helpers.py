import json
import re
import requests
import urllib
import logging
from django.conf import settings
from django.contrib.sites.models import RequestSite

logger = logging.getLogger('mumlife.api.helpers')


class APIResponse(dict):
    pass


class APIRequest(object):

    def __init__(self, request):
        self.request = request

    def _check_resource(self, resource):
        if not resource in ('message', 'event'):
            return APIResponse({'reason': 'Resource not implemented', 'status': 400})

    def get(self, **kwargs):
        resource = kwargs.get('resource')
        if not resource:
            return APIResponse({'reason': 'Resource name is required', 'status': 400})

        self._check_resource(resource)
        params = {'format': 'json'}

        if resource == 'message':
            res_loc = 'messages'
            search_query = urllib.quote(kwargs.get('search')) if \
                           kwargs.get('search') else ''
        elif resource == 'event':
            res_loc = 'messages'
            search_query = urllib.quote(kwargs.get('search')) if \
                           kwargs.get('search') else ''
            params['range'] = kwargs.get('range')
            params['events'] = 'true'

        if re.search(r'http:|https:', settings.API_URL) is None:
            site = RequestSite(self.request)
            protocol = 'https' if self.request.is_secure() else 'http'
            url = '{}://{}{}{}/1/{}'.format(protocol,
                                            site.domain,
                                            settings.API_URL,
                                            res_loc,
                                            search_query)
        else:
            url = '{}{}/1/{}'.format(settings.API_URL,
                                     res_loc,
                                     search_query)


        # the API uses session authentication
        try:
            cookies = {
                'sessionid': self.request.COOKIES[settings.SESSION_COOKIE_NAME],
                'csrftoken': self.request.COOKIES[settings.CSRF_COOKIE_NAME]
            }
        except KeyError:
            # 'csrftoken' is not set by the Test Runner,
            # so this will fail
            return APIResponse({'reason': 'Test run', 'status': 400})
        try:
            r = requests.get(url, verify=False, cookies=cookies, params=params)
        except requests.exceptions.ConnectionError:
            return APIResponse({'reason': 'Connection Error (Test run?)', 'status': 400})
        else:
            try:
                response = json.loads(r.text)
            except ValueError:
                response = {}

        return APIResponse(response)
