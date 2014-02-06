# mumlife/views.py
import logging
import json
import operator
import re
import requests
import urllib
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from tagging.models import Tag, TaggedItem
from longerusername.forms import AuthenticationForm
from mumlife import utils
from mumlife.models import Page, Member, Kid, Message, Friendships
from mumlife.forms import SignUpForm, MemberForm, KidForm, MessageForm

logger = logging.getLogger('mumlife.views')


"""
Public Views.
============================================================

"""

def home(request):
    if request.user.is_anonymous():
        context = {}
        # DEBUG: list all available users
        context['members'] = Member.objects.all()
        if request.method == 'POST':
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                if request.GET.has_key('next'):
                    return HttpResponseRedirect(request.GET['next'])
                return HttpResponseRedirect('/local/')
        else:
            form = AuthenticationForm()
        context['form'] = form
        t = loader.get_template('home.html')
        c = RequestContext(request, context)
        return HttpResponse(t.render(c))
    else:
        return HttpResponseRedirect('/local/')


def page(request, page):
    p = get_object_or_404(Page, slug=page)
    t = loader.get_template('page.html')
    c = RequestContext(request, {
        'title': p.title,
        'body': p.body
    })
    return HttpResponse(t.render(c))


"""
Members Views.
============================================================

"""

@login_required
def feed(request, tagstring=''):
    context = {}
    if request.method == 'POST' and request.POST.has_key('terms'):
        tagstring = urllib.quote(request.POST['terms'])
        return HttpResponseRedirect('/local/{}'.format(tagstring))

    if not tagstring:
        tagstring = ''
    context['tagstring'] = tagstring

    account = request.user.get_profile()
    context['account'] = account

    # Fetch 1st page of results from the API using cookie authentication
    protocol = 'https' if request.is_secure() else 'http'
    url = '{}:{}messages/1/{}'.format(protocol, settings.API_URL, urllib.quote(tagstring))
    cookies = {
        'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
        'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
    }
    r = requests.get(url, verify=False, cookies=cookies, params={'format': 'json'})
    try:
        response = json.loads(r.text)
        context['total'] = response['total']
        context['results'] = response['html_content']
        context['next'] = response['next']
    except ValueError:
        context['total'] = 0
        context['results'] = ''
        context['next'] = ''

    # Format empty results message
    if not context['total']:
        data = {
            'STATIC_URL': settings.STATIC_URL
        }
        content = loader.render_to_string('tags/message-noresults.html', data)
        context['noresults'] = content
        
    t = loader.get_template('feed.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def events(request, tagstring=''):
    context = {}
    if request.method == 'POST' and request.POST.has_key('terms'):
        tagstring = urllib.quote(request.POST['terms'])
        return HttpResponseRedirect('/events/{}'.format(tagstring))

    if not tagstring:
        tagstring = ''
    context['tagstring'] = tagstring

    account = request.user.get_profile()
    context['account'] = account

    # Fetch 1st page of results from the API using cookie authentication
    protocol = 'https' if request.is_secure() else 'http'
    url = '{}:{}messages/1/{}'.format(protocol, settings.API_URL, urllib.quote(tagstring))
    cookies = {
        'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
        'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
    }
    params = {
        'format': 'json',
        'events': 'true'
    }
    if request.GET.has_key('range') and request.GET['range']:
        params['range'] = request.GET['range']
    else:
        # when no range is provided, we check whether one is stored in the cookie
        # cookie name: ml_range
        if request.COOKIES.has_key('ml_range') and request.COOKIES['ml_range']:
            # the cookie is set, redirect to the same page,
            # appended with the stored range
            url = '/events/{}?range={}'.format(urllib.quote(tagstring), request.COOKIES['ml_range'])
            return HttpResponseRedirect(url)
    r = requests.get(url, verify=False, cookies=cookies, params=params)
    try:
        response = json.loads(r.text)
        context['total'] = response['total']
        context['results'] = response['html_content']
        context['next'] = response['next']
    except ValueError:
        context['total'] = 0
        context['results'] = ''
        context['next'] = ''

    t = loader.get_template('events.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def messages(request):
    context = {}

    account = request.user.get_profile()
    context['account'] = account
    context['friends'] = account.get_friends(Friendships.APPROVED)

    # Fetch 1st page of results from the API using cookie authentication
    protocol = 'https' if request.is_secure() else 'http'
    url = '{}:{}messages/1/{}'.format(protocol, settings.API_URL, '@private')
    cookies = {
        'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
        'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
    }
    r = requests.get(url, verify=False, cookies=cookies, params={'format': 'json'})
    try:
        response = json.loads(r.text)
        context['total'] = response['total']
        context['results'] = response['html_content']
        context['next'] = response['next']
    except ValueError:
        context['total'] = 0
        context['results'] = ''
        context['next'] = ''

    # Format empty results message
    if not context['total']:
        data = {
            'STATIC_URL': settings.STATIC_URL
        }
        content = loader.render_to_string('tags/message-noprivates.html', data)
        context['noresults'] = content

    t = loader.get_template('messages.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def notifications(request):
    account = request.user.get_profile()
    context = {
        'account': account
    }

    # Notifications are processed by MumlifeMiddleware
    if request.META.has_key("MUMLIFE_NOTIFICATIONS") and request.META["MUMLIFE_NOTIFICATIONS"]:
        response = request.META["MUMLIFE_NOTIFICATIONS"]
        context['total'] = response['total']
        context['results'] = response['html_content']
        # Reset account notifications
        account.notifications.reset(response)
    else:
        context['noresults'] = 'You do not have any notifications.'

    t = loader.get_template('tags/notifications.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def write(request):
    t = loader.get_template('write.html')
    c = RequestContext(request)
    return HttpResponse(t.render(c))


@login_required
def post(request):
    account = request.user.get_profile()
    # Messages are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context = {
        'account': account,
        'form': MessageForm()
    }
    t = loader.get_template('post.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def post_event(request):
    account = request.user.get_profile()
    # Events are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context = {
        'account': account,
        'form': MessageForm()
    }
    t = loader.get_template('event.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def edit_event(request, event_id):
    message = get_object_or_404(Message, pk=event_id)
    if message.member != request.user.get_profile():
        # Only the creator can edit its own events
        raise Http404
    if not message.eventdate:
        # Only events can be edited
        raise Http404
    account = request.user.get_profile()
    context = {
        'account': account,
        'edit_mode': True,
        'event_id': event_id
    }
    # Messages are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context['form'] = MessageForm(instance=message)
    t = loader.get_template('event.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def message(request, mid, eventmonth=None, eventday=None):
    account = request.user.get_profile()
    message = get_object_or_404(Message, pk=mid)
    formatted_message = message.format(viewer=request.user.get_profile())
    if eventmonth and eventday:
        formatted_message['eventmonth'] = eventmonth
        formatted_message['eventday'] = eventday
    context = {
        'account': account,
        'result': formatted_message
    }
    # back button
    backlink = 'local/'
    if message.eventdate:
        backlink = 'events/'
    elif message.visibility == Message.PRIVATE:
        backlink = 'messages/'
    elif message.visibility == Message.FRIENDS:
        backlink = 'local/@friends'
    elif message.area != account.area:
        backlink = 'local/@global'
    context['back'] = '{}{}'.format(settings.SITE_URL, backlink)

    t = loader.get_template('message.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def members(request, tagstring=''):
    account = request.user.get_profile()
    context = {
        'account': account
    }

    if request.method == 'POST' and request.POST.has_key('terms'):
        tagstring = urllib.quote(request.POST['terms'])
        return HttpResponseRedirect('/members/{}'.format(tagstring))

    tagstring = re.sub(r'\s\s*', '', tagstring)
    if not tagstring:
        # No tags: return them all
        members = Member.objects.all()
    else:
        context['tagstring'] = tagstring
        tags = utils.Extractor(tagstring).extract_tags()
        query_tags = Tag.objects.filter(name__in=tags.values())
        members = TaggedItem.objects.get_by_model(Member, query_tags)

    # Exclude logged-in user & Administrators
    members = members.exclude(user=request.user) \
                     .exclude(user__groups__name='Administrators')

    # Convert to list of dictionaries, so that we can order them by key
    members = [member.format(viewer=account) for member in members]

    # Order by decreasing distance
    members = sorted(members, key=operator.itemgetter('distance-key'))
    context['members'] = members

    t = loader.get_template('members.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def profile(request, slug=None):
    account = request.user.get_profile()
    if slug:
        try:
            member = Member.objects.get(slug__exact=slug)
            member = member.format(viewer=account)
        except Member.DoesNotExist:
            raise Http404
    else:
        member = account.format(viewer=account)

    context = {
        'account': account,
        'member': member
    }

    t = loader.get_template('profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def profile_edit(request, section=None, kid=None):
    account = request.user.get_profile()
    context = {
        'account': account
    }

    if section == 'account':
        if request.method == 'POST':
            form = MemberForm(request.POST, instance=account)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/profile/edit')
            context['form'] = form
        else:
            context['form'] = MemberForm(instance=account)
        template_name = 'profile_edit_account.html'

    elif section == 'kids':
        # New Kid form
        if request.method == 'POST':
            newkid_form = KidForm(request.POST)
            if newkid_form.is_valid():
                kid = newkid_form.save()
                kid.parents.add(account)
                return HttpResponseRedirect('/profile/edit/kids')
            context['form'] = newkid_form
        else:
            context['form'] = KidForm()
        template_name = 'profile_edit_kids.html'

    elif section == 'kid':
        try:
            kid = Kid.objects.get(pk=kid)
            if account not in kid.parents.all():
                raise Http404
            context['kid'] = kid
            if request.method == 'POST':
                form = KidForm(request.POST, instance=kid)
                if form.is_valid():
                    form.save()
                    return HttpResponseRedirect('/profile/edit/kids')
                context['form'] = form
            else:
                context['form'] = KidForm(instance=kid)
            template_name = 'profile_edit_kid.html'
        except Kid.DoesNotExist:
            raise Http404

    elif section == 'interests':
        context['form'] = MemberForm(instance=account)
        # popular interests
        popular = Tag.objects.usage_for_model(Member, counts=True, min_count=1)
        popular = sorted(popular, key=operator.attrgetter('count'), reverse=True)
        interests = Tag.objects.get_for_object(account)
        # only display tags not included in the account's ineterest
        intersection = filter(lambda x: x not in interests, popular)
        context['popular'] = intersection
        template_name = 'profile_edit_interests.html'

    elif section == 'preferences':
        context['form'] = MemberForm(instance=account)
        template_name = 'profile_edit_preferences.html'

    elif section == 'friends':
        # Friend requests
        friend_requests = []
        for friend in account.get_friend_requests().all():
            friend_requests.append(friend.from_member)
        if friend_requests:
            context['friend_requests'] = friend_requests
        # Friends
        friends = account.get_friends(Friendships.APPROVED)
        if friends:
            context['friends'] = friends
        # Blocked requests
        blocked_requests = account.get_friends(Friendships.BLOCKED)
        if blocked_requests:
            context['blocked_requests'] = blocked_requests
        template_name = 'profile_edit_friends.html'

    else:
        template_name = 'profile_edit.html'

    t = loader.get_template(template_name)
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))
