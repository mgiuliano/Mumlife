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
from mumlife.models import Member, Kid, Message
from mumlife.forms import MemberForm, KidForm, MessageForm
from mumlife.engines import NotificationEngine, SearchEngine

logger = logging.getLogger('mumlife.views')


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
                return HttpResponseRedirect('/s/')
        else:
            form = AuthenticationForm()
        context['form'] = form
        t = loader.get_template('home.html')
        c = RequestContext(request, context)
        return HttpResponse(t.render(c))
    else:
        return HttpResponseRedirect('/s/')


@login_required
def search(request, tagstring=''):
    context = {}
    if request.method == 'POST' and request.POST.has_key('terms'):
        tagstring = urllib.quote(request.POST['terms'])
        return HttpResponseRedirect('/s/{}'.format(tagstring))

    if not tagstring:
        tagstring = ''
    context['tagstring'] = tagstring

    account = request.user.get_profile()
    context['account'] = account

    # Fetch 1st page of results from the API using cookie authentication
    url = '{}messages/1/{}'.format(settings.API_URL, tagstring)
    cookies = {
        'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
        'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
    }
    r = requests.get(url, cookies=cookies, params={'format': 'json'})
    response = json.loads(r.text)

    context['total'] = response['total']
    context['results'] = response['content']
    context['next'] = response['next']
        
    t = loader.get_template('search.html')
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
    url = '{}messages/1/{}'.format(settings.API_URL, tagstring)
    cookies = {
        'sessionid': request.COOKIES[settings.SESSION_COOKIE_NAME],
        'csrftoken': request.COOKIES[settings.CSRF_COOKIE_NAME]
    }
    r = requests.get(url, cookies=cookies, params={'format': 'json', 'events': 'true'})
    response = json.loads(r.text)

    context['total'] = response['total']
    context['results'] = response['content']
    context['next'] = response['next']

    t = loader.get_template('events.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def notifications(request):
    account = request.user.get_profile()
    notifications = NotificationEngine(account=account).get()
    context = {
        'account': account
    }
    context.update(notifications)
    t = loader.get_template('notifications.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def write_message(request):
    account = request.user.get_profile()
    context = {
        'account': account,
        'api_url': settings.API_URL
    }
    # Messages are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context['form'] = MessageForm()
    t = loader.get_template('write_message.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def create_event(request):
    account = request.user.get_profile()
    context = {
        'account': account,
        'api_url': settings.API_URL
    }
    # Messages are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context['form'] = MessageForm()
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
        'edit_mode': True,
        'event_id': event_id,
        'account': account,
        'api_url': settings.API_URL,
    }
    # Messages are created using the API,
    # so there is no need to handle the POST action here.
    # we use the MessageForm for re-usability
    context['form'] = MessageForm(instance=message)
    t = loader.get_template('event.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def message(request, mid):
    account = request.user.get_profile()
    message = get_object_or_404(Message, pk=mid)
    context = {
        'account': account,
        'api_url': settings.API_URL,
        'result': message.format(viewer=request.user.get_profile())
    }

    t = loader.get_template('message.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def members(request, tagstring=''):
    account = request.user.get_profile()
    context = {
        'account': account,
        'api_url': settings.API_URL,
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
        #context['tags'] = [{'key': tag[0], 'value': tag[1]} for tag in tags.items()]
        query_tags = Tag.objects.filter(name__in=tags.values())
        members = TaggedItem.objects.get_by_model(Member, query_tags)

    # Exclude logged-in user
    members = members.exclude(user=request.user)

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
        'member': member,
        'api_url': settings.API_URL
    }

    t = loader.get_template('profile.html')
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))


@login_required
def profile_edit(request, section=None, kid=None):
    account = request.user.get_profile()
    context = {
        'account': account,
        'api_url': settings.API_URL
    }

    if section == 'account':
        context['api_url'] = context['api_url'] + 'members/'
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
            context['api_url'] = context['api_url'] + 'kids/'
            context['form'] = KidForm(instance=kid)
            template_name = 'profile_edit_kid.html'
        except Kid.DoesNotExist:
            raise Http404
    elif section == 'interests':
        context['api_url'] = context['api_url'] + 'members/'
        context['form'] = MemberForm(instance=account)
        # Popular interests
        popular = Tag.objects.usage_for_model(Member, counts=True, min_count=1)
        popular = sorted(popular, key=operator.attrgetter('count'), reverse=True)
        interests = Tag.objects.get_for_object(account)
        # only display tags not included in the account's ineterest
        intersection = filter(lambda x: x not in interests, popular)
        context['popular'] = intersection
        template_name = 'profile_edit_interests.html'
    elif section == 'preferences':
        context['api_url'] = context['api_url'] + 'members/'
        context['form'] = MemberForm(instance=account)
        template_name = 'profile_edit_preferences.html'
    else:
        friend_requests = []
        for friend in account.get_friend_requests().all():
            friend_requests.append(friend.from_member)
        if friend_requests:
            context['friend_requests'] = friend_requests
        template_name = 'profile_edit.html'

    t = loader.get_template(template_name)
    c = RequestContext(request, context)
    return HttpResponse(t.render(c))
