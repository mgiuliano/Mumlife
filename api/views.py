# api/views.py
import logging
import copy
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
from mumlife.engines import SearchEngine, NotificationEngine
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
        'messages': reverse('messages-list', request=request, format=format, args=[1,'']),
        'notifications': reverse('notifications-list', request=request, format=format),
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


class MessageListView(views.APIView):
    """
    List messages for the logged-in user.
    Results are paginated.

    """
    permissions = (permissions.IsAuthenticated,)

    def get(self, request, page=1, terms='', format=None):
        try:
            page = 1 if page < 1 else int(page)
        except ValueError:
            page = 1

        account = self.request.user.get_profile()
        se = SearchEngine(account=account)
        
        # Adding 'events' as a query parameter tells us to return events only.
        show_events = False
        distance_range = 9999 # Nationwide
        if request.GET.has_key('events'):
            # Events are fetched in a different way
            # particularly, the results need to be in a specific distance range
            show_events = True
            if request.GET.has_key('range'):
                try:
                    distance_range = int(request.GET['range'])
                    if distance_range == 0:
                        distance_range = 9999 # Nationwide
                except ValueError:
                    # the value passed was not an integer
                    pass
            all_results = se.search_events(terms)
        else:
            all_results = se.search_messages(terms)

        # Pre-process results
        messages = [m.format(viewer=account) for m in all_results]

        # Event-only: exclude out-of-range events
        if show_events:
            messages = [m for m in messages if m['distance-key'] <= distance_range]

        # Return range according to page
        total = len(messages)
        start = (page - 1) * settings.PAGING
        end = start + settings.PAGING
        results = messages[start:end]

        # Record the last result's last message,
        # this result will be None for the first page.
        if start <= settings.PAGING:
            last_message = None
        else:
            try:
                last_message = messages[start-1]
            except AssertionError:
                # AssertionError is raise when using negative indexing
                last_message = None
            except IndexError:
                # IndexError is raised when the result set is empty
                last_message = None

        # Determine whether this was the last page
        # we are on the last page when the last page is greater or equal
        # to the total number of results
        next_page = '1/messages/{}/{}'.format(page + 1, terms) if end < total else ''
        if next_page and show_events:
            # we add the 'events' back to the querystring for the next page link
            next_page = '{}{}'.format(next_page, '?events')
            # we also add the range
            next_page = '{}{}{}'.format(next_page, '&range=', distance_range)

        # Format results
        html_content = ''
        previous_day = None
        template = 'tags/event.html' if show_events else 'tags/message.html'
        for message in results:
            if show_events:
                # determine whether to display the day heading
                day = message['eventdate']
                if not previous_day or previous_day != day:
                    # we check that the heading was not already displayed
                    # by results from the previous page
                    if not last_message or message['eventdate'] != last_message['eventdate']:
                        message['heading'] = message['eventdate']
                previous_day = day
            message['STATIC_URL'] = settings.STATIC_URL
            message['SITE_URL'] = settings.SITE_URL
            html_content += loader.render_to_string(template, message)

        response = {
            'total': total,
            'next': next_page,
            'messages': results,
            'html_content': html_content,
        }
        return Response(response)


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
        eventenddate = request.DATA['eventenddate'] if request.DATA.has_key('eventenddate') else None
        location = request.DATA['location'] if request.DATA.has_key('location') else None
        if location:
            postcode = utils.Extractor(location).extract_postcode()
            if postcode:
                # the postcode will be a valid postcode at this stage,
                # if one was provided.
                # we add the postcode area to the list of tags
                tags = '#{} {}'.format(postcode.split(' ')[0].lower(), tags)
        occurrence = request.DATA['occurrence'] if request.DATA.has_key('occurrence') else Message.OCCURS_ONCE
        occurs_until = request.DATA['occurs_until'] \
                       if request.DATA.has_key('occurs_until') and request.DATA['occurs_until'] \
                       else None

        # remove tags duplicates
        tags = ' '.join(list(set(tags.split(' '))))

        # create message
        try:
            message = Message.objects.create(body=request.DATA['body'],
                                         member=member,
                                         area=member.area,
                                         name=name,
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
            elif key == 'body':
                # reset tags
                tags = utils.Extractor(value).extract_tags()
                tags = tags.values()
                tags.append('#{}'.format(request.user.get_profile().area.lower()))
                tags = list(set(tags))
                message.tags = ' '.join(tags)
            if getattr(message, key) != value:
                setattr(message, key, value)
            message.save()

        # serialize message to return
        serializer = MessageSerializer(message)
        return Response(serializer.data)


class MessageView(generics.RetrieveUpdateAPIView):
    model = Message
    serializer_class = MessageSerializer
    permissions = (permissions.IsAdminUser,)


class NotificationListView(views.APIView):
    """
    List all notifications for the logged-in user.

    """
    permissions = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        account = self.request.user.get_profile()
        r = NotificationEngine(account=account).get()

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
            html_data['SITE_URL'] = settings.SITE_URL
            html_content += loader.render_to_string(template, html_data)

        response = {
            'total': r['count'],
            'results': r['results'],
            'html_content': html_content,
        }
        return Response(response)
