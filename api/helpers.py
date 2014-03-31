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
        if resource not in ('message', 'event', 'member', 'notification'):
            return False
        return True

    def get(self, **kwargs):
        resource = kwargs.get('resource')
        if not resource:
            return json.dumps(APIResponse({'reason': 'Resource name is required', 'status': 400}))
        if not self._check_resource(resource):
            return json.dumps(APIResponse({'reason': 'Resource not implemented', 'status': 400}))

        params = {'format': 'json'}

        if resource == 'message':
            res_loc = 'messages/'
            params['search'] = kwargs.get('search')
        elif resource == 'event':
            params['range'] = kwargs.get('range')
            params['events'] = 'true'
            params['search'] = kwargs.get('search')
            res_loc = 'messages/'

        elif resource == 'member':
            res_loc = 'members/'
            params['search'] = kwargs.get('search')

        elif resource == 'notification':
            res_loc = 'notifications/'

        if re.search(r'http:|https:', settings.API_URL) is None:
            site = RequestSite(self.request)
            protocol = 'https' if self.request.is_secure() else 'http'
            url = '{}://{}{}{}'.format(protocol,
                                       site.domain,
                                       settings.API_URL,
                                       res_loc)
        else:
            url = '{}{}'.format(settings.API_URL, res_loc)

        # the API uses session authentication
        try:
            cookies = {
                'sessionid': self.request.COOKIES[settings.SESSION_COOKIE_NAME],
                'csrftoken': self.request.COOKIES[settings.CSRF_COOKIE_NAME]
            }
        except KeyError:
            # 'csrftoken' is not set by the Test Runner,
            # so this will fail
            return json.dumps(APIResponse({'reason': 'Test run', 'status': 400}))
        try:
            r = requests.get(url, verify=False, cookies=cookies, params=params)
        except requests.exceptions.ConnectionError:
            return json.dumps(APIResponse({'reason': 'Connection Error (Test run?)', 'status': 400}))
        else:
            try:
                response = json.loads(r.text)
            except ValueError:
                response = {}

        return json.dumps(APIResponse(response))
