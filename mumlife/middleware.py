# mumlife/middleware.py
import logging
import json
import re
import requests
from django.conf import settings
from django.middleware.csrf import get_token
from django.contrib.sites.models import RequestSite
from mumlife import views
from api.helpers import APIRequest

logger = logging.getLogger('mumlife.middleware')


class MumlifeMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Fetch notifications from the API
        __processed_views = dir(views)
        # make sure this view is not processed,
        # or we'll have ourself an infinite loop
        if request.user.is_authenticated() and view_func.__name__ in __processed_views:
            params = {
                'resource': 'notification',
            }
            response = APIRequest(request).get(**params)
            request.META["MUMLIFE_NOTIFICATIONS"] = json.loads(response)
        return None


def request(request):
    meta = {
        'API_URL': settings.API_URL,
        'DEBUG': settings.DEBUG,
    }

    if request.user.is_authenticated():
        # The account notifications hold the ones already read
        try:
            member_notifications = request.user.profile.notifications
        except:
            # legacy - users with no notifications related objects will fail
            read = 0
        else:
            # make sure the list of stored notifications is updated before using it
            member_notifications.update()
            read = member_notifications.total
        # We retrieve all notifications from the API,
        # whose results have already been fetched by the middleware view processor;
        # in META["MUMLIFE_NOTIFICATIONS"]
        notifications = request.META.get("MUMLIFE_NOTIFICATIONS")
        if notifications is not None:
            meta['notifications'] = notifications
            total = notifications.get('total', 0)
        else:
            total = 0
        # Process difference (i.e. unread ones)
        unread = total - read
        if unread < 0:
            unread = 0
        meta['new_notifications'] = True if unread else False
    return meta
