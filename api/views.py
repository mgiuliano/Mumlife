# api/views.py
import logging
import copy
import datetime
import operator
import re
from django.conf import settings
from django.core.exceptions import PermissionDenied
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
from tagging.models import Tag, TaggedItem
from mumlife import utils
from mumlife.models import Member, Kid, Friendships, Message
from api.serializers import MemberSerializer, \
                            KidSerializer, \
                            FriendshipsSerializer, \
                            MessageSerializer, \
                            EventSerializer

logger = logging.getLogger('mumlife.api')


@api_view(('GET',))
@permission_classes((permissions.IsAdminUser, ))
def api_root(request, format=None):
    return Response({
        'members': reverse('members-list', request=request, format=format),
        'kids': reverse('kids-list', request=request, format=format),
        'friendships': reverse('friendships-list', request=request, format=format),
        'messages': reverse('messages-list', request=request, format=format),
        'notifications': reverse('notifications-list', request=request, format=format),
    })


class MemberListView(generics.ListAPIView):
    """List all members.

    The distance returned is in meters.
    The query can be filtered by a lits of Tags (tagging.models.Tag).
    """
    model = Member
    serializer_class = MemberSerializer
    paginate_by = settings.MEMBERS_PER_PAGE
    
    def list(self, request, *args, **kwargs):
        search = request.QUERY_PARAMS.get('search', None)
        if search:
            search = re.sub(r'\s\s*', ' ', search)
            search = re.sub(r'#|%23', '', search)
            tags = search.split(',')
            query_tags = Tag.objects.filter(name__in=tags)
        else:
            query_tags = None
        member = request.user.get_profile()
        self.object_list = Member.objects.with_distance_from(viewer=member,
                                                             query_tags=query_tags)

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        # Override serialization with Member.format()
        # Doing the formatting here means the operation is only calculated
        # for the slice MEMBERS_PER_PAGE, instead of the entire QuerySet
        results = serializer.data['results'][:]
        serializer.data['results'] = []
        for obj in results:
            _member = Member.objects.get(pk=obj['id'])
            _member.distance = obj['distance']
            serializer.data['results'].append(_member.format(member))

        return Response(serializer.data)


class MemberView(generics.RetrieveUpdateAPIView):
    """Allows partial update (PUT/PATCH).

    A member can only view/update its own account.
    Members cannot be deleted through the API.
    """
    model = Member
    serializer_class = MemberSerializer

    def get_object(self):
        obj = super(MemberView, self).get_object()
        if obj.user != self.request.user:
            # A user can only view/update its own account
            raise PermissionDenied
        return obj


class KidListView(generics.ListAPIView):
    """List all kids."""
    queryset = Kid.objects.all()
    serializer_class = KidSerializer
    permissions = (permissions.IsAdminUser,)


class KidView(generics.RetrieveUpdateAPIView):
    """Allows partial update (PUT/PATCH).

    A member can only view/update its own kids.
    Kids cannot be deleted through the API.
    """
    model = Kid
    serializer_class = KidSerializer

    def get_object(self):
        obj = super(KidView, self).get_object()
        if not self.request.user.get_profile() in obj.parents.all():
            # A user can only view/update its own kids
            raise PermissionDenied
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
            
            #return Response({'detail': 'Already Exists'}, status=status.HTTP_409_CONFLICT)
        except Friendships.DoesNotExist:
            # we create the friendship request
            response = super(FriendshipsListView, self).post(request=request, format=format)
            return response
        else:
            # update friendship
            friendship.status = request.DATA['status']
            friendship.save()
            # and manually fire the post event to update the symmetrical relationship
            self.post_save(friendship, created=True)
            serializer = FriendshipsSerializer(friendship)
            return Response(serializer.data)

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
                elif obj.status == Friendships.BLOCKED:
                    # when a relationship is blocked, the symmetrical relationship is simply removed
                    friendship.delete()
                elif obj.status == Friendships.PENDING:
                    # when both relations are pending, they must have requested a friendship at the same time.
                    # in this case, set the both as APPROVED
                    # this will happen when friend requests are approved
                    if friendship.status != Friendships.BLOCKED:
                        friendship.status = Friendships.APPROVED
                        friendship.save()
                        obj.status = Friendships.APPROVED
                        obj.save()
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


class MessageListView(generics.ListAPIView):
    """List messages for the logged-in user.

    Results are paginated.
    """
    model = Message
    serializer_class = MessageSerializer
    paginate_by = settings.MESSAGES_PER_PAGE

    def list(self, request, *args, **kwargs):
        search = request.QUERY_PARAMS.get('search', None)
        member = request.user.get_profile()

        # Adding 'events' as a query parameter tells us to return events only.
        show_events = request.QUERY_PARAMS.get('events', None)
        distance_range = None # Nationwide
        if show_events is not None:
            # Events are fetched in a different way
            # particularly, the results need to be in a specific distance range
            range_ = request.QUERY_PARAMS.get('range', None)
            if range_ is not None:
                try:
                    # the range can be sent in miles or kilometers
                    # if the range is set in miles, we need to convert is to meters
                    distance_range = float(range_)
                    if member.units == 1:
                        distance_range /= 0.6214
                    distance_range *= 1000
                except ValueError:
                    # the value passed was not an integer
                    pass
            self.object_list = member.get_events(search=search,
                                                 distance_range=distance_range)
            self.serializer_class = EventSerializer
        else:
            self.object_list = member.get_messages(search=search)

        # Switch between paginated or standard style responses
        page = self.paginate_queryset(self.object_list)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list, many=True)

        # Override serialization with Message.format()
        # Doing the formatting here means the operation is only calculated
        # for the slice MESSAGES_PER_PAGE, instead of the entire QuerySet
        results = serializer.data['results'][:]
        serializer.data['results'] = []
        for obj in results:
            _message = Message.objects.get(pk=obj['id'])
            # This is not the nicest way of doing it, but all data
            # added for occurences will be destroyed in the new Message object,
            # as well as the distance we just calculated.
            # So we need to add those back in.
            if show_events is not None:
                _message.distance = obj['distance']
                _message.eventdate = obj['eventdate']
            serializer.data['results'].append(_message.format(member))

        return Response(serializer.data)


class MessagePostView(APIView):
    """Provide PUT and PATCH methods.

    Post new Message or Reply (PUT),
    Partial update (PATCH).
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

        # picture
        picture = request.DATA['picture'] if request.DATA.has_key('picture') else None

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

        # add inline tags to tag list
        tags = utils.Extractor(request.DATA['body']).extract_tags()
        tags = tags.values()
        # additional tags can be specified.
        # even when an empty string is posted, we do not add the default tag.
        if request.DATA.has_key('tags'):
            if request.DATA['tags']:
                tags.extend(request.DATA['tags'].split())
        else:
            # when no tags are specified, we include the member area as a tag
            tags.append('#{}'.format(member.area.lower()))
    
        # optional event data
        name = request.DATA['name'] if request.DATA.has_key('name') else None
        eventdate = request.DATA['eventdate'] if request.DATA.has_key('eventdate') else None
        eventenddate = request.DATA['eventenddate'] if request.DATA.has_key('eventenddate') else None
        location = request.DATA['location'] if request.DATA.has_key('location') else None
        if location:
            postcode = utils.Extractor(location).extract_postcode()
            if postcode:
                # the postcode will be a valid postcode at this stage,
                # if one was provided.
                # we add the postcode area to the list of tags
                postcode_area = postcode.split()[0].lower()
                tags.append('#{}'.format(postcode_area))
        occurrence = request.DATA['occurrence'] if request.DATA.has_key('occurrence') else Message.OCCURS_ONCE
        occurs_until = request.DATA['occurs_until'] \
                       if request.DATA.has_key('occurs_until') and request.DATA['occurs_until'] \
                       else None

        # remove tags duplicates
        tags = list(set(tags))
        tags = sorted(tags)
        tags = ' '.join(tags)

        # create message
        try:
            message = Message.objects.create(body=request.DATA['body'],
                                         member=member,
                                         area=member.area,
                                         name=name,
                                         picture=picture,
                                         location=location,
                                         eventdate=eventdate,
                                         eventenddate=eventenddate,
                                         visibility=visibility,
                                         occurrence=occurrence,
                                         occurs_until=occurs_until,
                                         is_reply = True if reply_to else False,
                                         reply_to=reply_to,
                                         recipient=recipient,
                                         tags=tags)
        except Exception as e:
            logger.error(e)
            return Response()

        # serialize message to return
        serializer = MessageSerializer(message)
        return Response(serializer.data)

    def patch(self, request, format=None):
        try:
            message = Message.objects.get(pk=request.DATA['id'])
        except Message.DoesNotExist:
            raise Http404

        if message.member != request.user.get_profile():
            # only the creator can edit its own events
            raise PermissionDenied

        for key, value in request.DATA.items():
            if value is None or key in ('id',):
                continue
            if key == 'visibility':
                value = long(value)
            if key == 'occurrence':
                value = int(value)
            elif key == 'eventdate':
                # make datetime aware
                value = timezone.make_aware(datetime.datetime.strptime(value, '%Y-%m-%d %H:%M'), timezone.get_default_timezone())
            elif key == 'occurs_until':
                if value:
                    # make date aware
                    value = timezone.make_aware(datetime.datetime.strptime(value, '%Y-%m-%d'), timezone.get_default_timezone())
                else:
                    # clear date
                    value = None
            if getattr(message, key) != value:
                setattr(message, key, value)

        # reset tags
        tags = utils.Extractor(message.body).extract_tags().values()
        tags.append('#{}'.format(request.user.get_profile().area.lower()))
        if message.location:
            postcode = utils.Extractor(message.location).extract_postcode()
            if postcode:
                tags.append('#{}'.format(postcode.split()[0].lower()))
        tags = list(set(tags))
        message.tags = ' '.join(tags)

        # save changes
        message.save()

        # serialize message to return
        serializer = MessageSerializer(message)
        return Response(serializer.data)


class MessageView(generics.RetrieveUpdateDestroyAPIView):
    model = Message
    serializer_class = MessageSerializer

    def get_object(self):
        obj = super(MessageView, self).get_object()
        if obj.member != self.request.user.get_profile():
            # A user can only view/update/destroy its own messages
            raise PermissionDenied
        return obj


class NotificationListView(views.APIView):
    """List all notifications for the logged-in user."""
    permissions = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        account = self.request.user.get_profile()
        r = account.get_notifications()

        # Format results
        html_content = ''
        notification_events = account.notifications.events.all()
        notification_threads = account.notifications.threads.all()
        for result in r['results']:
            if result['type'] in ('events', 'threads'):
                # ManyToMany fields, notification is read if in list
                if result['type'] == 'events':
                    read = result['event']['id'] in \
                           [m['id'] for m in notification_events.values('id')]
                else:
                    read = True
                    for message in result['thread']['messages']:
                        if message['id'] not in [m['id'] for m in notification_threads.values('id')]:
                            read = False
                            break
            else:
                read = getattr(account.notifications, result['type'])
            template = 'tags/notification-{}.html'.format(result['type'])
            html_data = copy.deepcopy(result)
            html_data['read'] = read
            html_data['STATIC_URL'] = settings.STATIC_URL
            html_content += loader.render_to_string(template, html_data)

        response = {
            'total': r['count'],
            'results': r['results'],
            'html_content': html_content,
        }
        return Response(response)
