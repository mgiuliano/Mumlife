# api/views.py
import logging
import datetime
import operator
from django.conf import settings
from django.http import Http404
from django.template import loader
from django.utils import timezone
from rest_framework import status
from rest_framework import views
from rest_framework import generics
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from mumlife import utils
from mumlife.models import Member, Kid, Friendships, Message
from mumlife.engines import NotificationEngine, SearchEngine
from api.serializers import MemberSerializer, \
                            KidSerializer, \
                            FriendshipsSerializer, \
                            MessageSerializer

logger = logging.getLogger('mumlife.api')

@api_view(('GET',))
@permission_classes((permissions.IsAdminUser, ))
def api_root(request, format=None):
    return Response({
        'members': reverse('members-list', request=request, format=format),
        'kids': reverse('kids-list', request=request, format=format),
        'friendships': reverse('friendships-list', request=request, format=format),
        'messages': reverse('messages-list', request=request, format=format),
    })


class MemberListView(generics.ListAPIView):
    """
    List all members (admin read-only).

    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permissions = (permissions.IsAdminUser,)


class MemberView(generics.RetrieveUpdateAPIView):
    """
    Allows partial update (PUT/PATCH).

    A member can only view/update its own account.

    Members cannot be deleted through the API.

    """
    model = Member
    serializer_class = MemberSerializer

    def get_object(self):
        obj = super(MemberView, self).get_object()
        if obj.user != self.request.user:
            # A user can only view/update its own account
            raise Http404
        return obj


class KidListView(generics.ListAPIView):
    """
    List all kids (admin read-only).

    """
    queryset = Kid.objects.all()
    serializer_class = KidSerializer
    permissions = (permissions.IsAdminUser,)


class KidView(generics.RetrieveUpdateAPIView):
    """
    Allows partial update (PUT/PATCH).

    A member can only view/update its own kids.

    Kids cannot be deleted through the API.

    """
    model = Kid
    serializer_class = KidSerializer

    def get_object(self):
        obj = super(KidView, self).get_object()
        if not self.request.user.get_profile() in obj.parents.all():
            # A user can only view/update its own kids
            raise Http404
        return obj


class FriendshipsListView(generics.ListCreateAPIView):
    model = Friendships
    serializer_class = FriendshipsSerializer

    def post(self, request, format=None):
        # Relationship to oneself is not allowed,
        # it doesn't even make sense
        if request.DATA['from_member'] == request.DATA['to_member']:
            return Response({'detail': 'Same member'}, status=status.HTTP_400_BAD_REQUEST)
        # Check whether the friendship already exists
        try:
            friendship = Friendships.objects.get(from_member=request.DATA['from_member'],
                                                 to_member=request.DATA['to_member'])
            return Response({'detail': 'Already Exists'}, status=status.HTTP_409_CONFLICT)
        except Friendships.DoesNotExist:
            # we create the friendship request
            response = super(FriendshipsListView, self).post(request=request, format=format)
            return response

    def post_save(self, obj, created=False):
        """
        Create the symmetrical friendship when object is created as APPROVED.
        The 'from_member > to_member' has just been created at this point.

        If the friendship relation already exists, update its status to APPROVED.
        This occurs when friendship requests are approved.

        """
        if created:
            # The relation has been created,
            # check if the symmetrical relation exists
            try:
                friendship = Friendships.objects.get(from_member=obj.to_member,
                                                     to_member=obj.from_member)
                if obj.status == Friendships.APPROVED:
                    # the request is APPROVED, so we force the symmetrical to be approved too
                    friendship.status = Friendships.APPROVED
                    friendship.save()
                elif obj.status == Friendships.PENDING:
                    # when both relations are pending, they must have requested a friendship at the same time.
                    # in this case, set the both as APPROVED
                    # this will happen when friend requests are approved
                    if friendship.status != Friendships.BLOCKED:
                        friendship.status = Friendships.APPROVED
                        friendship.save()
                        obj.status = Friendships.APPROVED
                        obj.save()
                elif obj.status == Friendships.BLOCKED:
                    # when the requested relation is blocked, we set the reverse relation as blocked
                    friendship.status = Friendships.BLOCKED
                    friendship.save()
            except Friendships.DoesNotExist:
                # the symmetrical relation does not exist
                # we force its creation anyway when the request as an APPROVED status
                # (shouldn't really happen, except maybe in the future if we need it)
                if obj.status == Friendships.APPROVED:
                    obj.to_member.add_friend(obj.from_member, Friendships.APPROVED)


class FriendshipView(generics.RetrieveUpdateDestroyAPIView):
    model = Friendships
    serializer_class = FriendshipsSerializer
    permissions = (permissions.IsAdminUser,)


class MessageListView(views.APIView):
    """
    List all messages (admin read-only).

    """
    permissions = (permissions.IsAuthenticated,)

    def get(self, request, page=1, terms='', format=None):
        try:
            page = 1 if page < 1 else int(page)
        except ValueError:
            page = 1

        events_only = False
        if request.GET.has_key('events') and request.GET['events'] == 'true':
            events_only = True

        account = self.request.user.get_profile()

        # Fetch Messages
        se = SearchEngine(account=account)
        results = se.search(terms)

        if events_only:
            results = [r for r in results if r.eventdate is not None and r.eventdate >= timezone.now()]
            results = sorted(results, key=operator.attrgetter('eventdate'));

        total = len(results)

        # Format messages
        messages = []
        previous_day = None
        for message in results:
            c = message.format(viewer=account)
            if events_only:
                day = c['eventday'] + ' ' + c['eventmonth']
                if not previous_day or previous_day != day:
                    c['heading'] = c['eventdate']
                    previous_day = day
            c['STATIC_URL'] = settings.STATIC_URL
            c['SITE_URL'] = settings.SITE_URL
            messages.append(c)

        # Return range according to page
        start = (page - 1) * settings.PAGING
        end = start + settings.PAGING
        results = messages[start:end]

        # Determine whether this was the last page
        # we are on the last page when the last page is greater or equal
        # to the total number of results
        next_page = '1/messages/{}'.format(page + 1) if end < total else ''

        # Format output
        content = ''
        template = 'tags/event.html' if events_only else 'tags/message.html'
        for message in results:
            content += loader.render_to_string(template, message)

        response = {
            'total': total,
            'next': next_page,
            'content': content,
        }
        return Response(response)


class MessageView(generics.RetrieveUpdateAPIView):
    model = Message
    serializer_class = MessageSerializer
    permissions = (permissions.IsAdminUser,)


class MessagePostView(APIView):
    """
    Post new Message or Reply.

    """
    def post(self, request, format=None):
        # message is required
        if not request.DATA.has_key('body') or not request.DATA['body']:
            return Response({'detail': "Message required."},
                            status=400,
                            exception=True)

        # the sender is always the logged-in user
        member = request.user.get_profile()

        # check for mid
        # if present, attach message as reply
        if request.DATA.has_key('mid'):
            try:
                reply_to = Message.objects.get(pk=int(request.DATA['mid']))
            except Notice.DoesNotExists:
                reply_to = None
        else:
            reply_to = None

        # visibility settings
        if reply_to:
            # replies inherit their parent's visibility
            visibility = reply_to.visibility
        elif request.DATA.has_key('visibility'):
            visibility = request.DATA['visibility']

        # is it a private message?
        recipient = None
        if visibility == Message.PRIVATE and request.DATA.has_key('recipient'):
            try:
                recipient = Member.objects.get(pk=request.DATA['recipient'])
            except Member.DoesNotExist:
                pass

        # add tags to message
        tags = utils.Extractor(request.DATA['body']).extract_tags()
        tags = ' '.join(tags.values())
        # include the member area as a tag
        tags = '#{} {}'.format(member.area.lower(), tags)

        # optional event data
        name = request.DATA['name'] if request.DATA.has_key('name') else None
        eventdate = request.DATA['eventdate'] if request.DATA.has_key('eventdate') else None
        location = request.DATA['location'] if request.DATA.has_key('location') else None

        # create message
        message = Message.objects.create(body=request.DATA['body'],
                                      member=member,
                                      area=member.area,
                                      name=name,
                                      location=location,
                                      eventdate=eventdate,
                                      visibility=visibility,
                                      is_reply = True if reply_to else False,
                                      reply_to=reply_to,
                                      recipient=recipient,
                                      tags=tags)

        # serialize message to return
        serializer = MessageSerializer(message)
        return Response(serializer.data)

    """
    Patch existing Message.

    """
    def patch(self, request, format=None):
        try:
            message = Message.objects.get(pk=request.DATA['id'])
        except Message.DoesNotExist:
            raise Http404

        if message.member != request.user.get_profile():
            # Only the creator can edit its own events
            raise Http404

        for key, value in request.DATA.items():
            if value is None or key in ('id',):
                continue
            if key == 'visibility':
                value = long(value)
            if key == 'eventdate':
                value = timezone.make_aware(datetime.datetime.strptime(value, '%Y-%m-%d %H:%M'), timezone.get_default_timezone())
            if key == 'body':
                # reset tags
                tags = utils.Extractor(value).extract_tags()
                tags = tags.values()
                tags.append('#{}'.format(request.user.get_profile().area.lower()))
                message.tags = ' '.join(tags)
            if getattr(message, key) != value:
                setattr(message, key, value)
            message.save()

        # serialize message to return
        serializer = MessageSerializer(message)
        return Response(serializer.data)
