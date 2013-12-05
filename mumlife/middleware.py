# mumlife/middleware.py
from django.conf import settings

def request(request):
    try:
        account = request.user.get_profile()
        notifications = account.get_friend_requests().count()
    except:
        notifications = 0
    meta = {
        'SITE_URL': settings.SITE_URL,
        'notifications': notifications
    }
    return meta
