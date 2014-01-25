# mumlife/engines.py
import logging
import operator
import re
from copy import deepcopy
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from tagging.models import Tag, TaggedItem
from dateutil.rrule import rrule, WEEKLY
from dateutil.relativedelta import relativedelta
from mumlife import utils
from mumlife.models import Message, Friendships

logger = logging.getLogger('mumlife.engines')


class SearchEngine(object):
    def __init__(self, account=None, verbose=False):
        self.account = account
        self.flag = '@local'
        self.verbose = verbose
    
    def search(self, terms='@local'):
        """
        Common initial search.
        Return a QuerySet object so that further filtering can be applied.

        """
        # whitespaces are not allowed, so get rid of them
        tagstring = re.sub(r'\s\s*', '', terms)
        if not tagstring:
            tagstring = '@local' # default search

        # extract flags @flags
        # only one flag is allowed. Exceptions will default to @local
        flags = utils.Extractor(tagstring).extract_flags()
        if not flags or len(flags) > 1:
            flags = ['@local']
        try:
            self.flag = flags[0]
        except IndexError:
            pass

        # extract hastags #hashtag
        tags = utils.Extractor(tagstring).extract_tags().values()
        if not tags:
            # return all messages
            messages = Message.objects.all()
        else:
            query_tags = Tag.objects.filter(name__in=tags)
            messages = TaggedItem.objects.get_by_model(Message, query_tags)

        # exclude replies
        messages = messages.exclude(is_reply=True)
        return messages

    def search_messages(self, terms='@local'):
        """
        Exclude ALL Events.
        Search rules:
            - search terms are matches against hashtags;
            - search for nothing returns local results;
            - @local (default) includes:
                - LOCAL & GLOBAL messages within account area
                - FRIENDS messages within account area, from account friends
                (using @local is redundant, as it is the default);
            - @global includes:
                - GLOBAL messages outside account area;
            - @friends includes:
                - FRIENDS messages in all areas, from account friends
            - @private includes:
                - PRIVATE messages sent to account, regardless of area or friendship

        """
        messages = self.search(terms=terms)

        # Exclude events
        messages = messages.exclude(eventdate__isnull=False)
        
        # @friends results
        if self.flag == '@friends':
            # OWN FRIENDS messages
            _own = Q(member=self.account, visibility=Message.FRIENDS)
            if self.verbose:
                print ' ... Own >>>', messages.filter(_own)
            # All messages from account friends
            members_friends = [f['id'] for f in self.account.get_friends(status=Friendships.APPROVED).values('id')]
            _friends = Q(member__id__in=members_friends,
                         visibility__in=[Message.LOCAL, Message.GLOBAL, Message.FRIENDS])
            if self.verbose:
                print ' ... Friends >>>', messages.filter(_friends)
            messages = messages.filter(_own | _friends)

        # @private results
        elif self.flag == '@private':
            # OWN PRIVATE messages
            _own = Q(member=self.account, visibility=Message.PRIVATE)
            if self.verbose:
                print ' ... Own >>>', messages.filter(_own)
            # PRIVATE messages sent to account, regardless of area
            _privates = Q(visibility=Message.PRIVATE, recipient=self.account)
            if self.verbose:
                print ' ... Privates >>>', messages.filter(_privates)
            messages = messages.filter(_own | _privates)

        # @global results
        elif self.flag == '@global':
            # GLOBAL messages outside account area
            _globals = Q(visibility=Message.GLOBAL) & ~Q(area=self.account.area)
            if self.verbose:
                print ' ... Globals >>>', messages.filter(_globals)
            messages = messages.filter(_globals)

        # @local results
        else:
            # LOCAL and GLOBAL messages within account area
            _locals = Q(visibility__in=[Message.LOCAL, Message.GLOBAL], area=self.account.area)
            if self.verbose:
                print ' ... Locals >>>', messages.filter(_locals)
            # FRIENDS messages within account area, from account friends
            members_friends = [f['id'] for f in self.account.get_friends(status=Friendships.APPROVED).values('id')]
            _friends = Q(member__id__in=members_friends,
                         visibility=Message.FRIENDS,
                         area=self.account.area)
            if self.verbose:
                print ' ... Friends >>>', messages.filter(_friends)
            messages = messages.filter(_locals | _friends)

        # order messages in reverse chronological order
        messages = messages.order_by('-timestamp')
        
        return list(messages.distinct())

    def search_events(self, terms=''):
        """
        All events are returned, regardless of the location of the sender/author.
        Events are ordered by Event Date, rather than Post Date, in chronological order.
        Events are upcoming (i.e. no past events).

        Recurring events are generated on-the-fly.

        """
        now = timezone.now()
        messages = self.search(terms=terms)

        # exclude non-events
        messages = messages.exclude(eventdate__isnull=True)

        # exclude past non-recurring events
        messages = messages.exclude(occurrence=Message.OCCURS_ONCE,
                                    eventdate__lt=now)

        messages = messages.distinct()
        events = list(messages)

        # we keep recurring events for now, as we will use them to create the occurrences
        # the occurences will then be filtered according to their dates
        for message in messages.all():
            if message.occurrence == Message.OCCURS_WEEKLY:
                # generate occurrence from today, on this week day,
                # at the the same time (hour, minutes, seconds)
                if message.occurs_until:
                    # when an end date is provided, we generate occurrences until that date only
                    # ---
                    # we have to convert date to datetime,
                    # then make the datetime aware.
                    # this is because Django stores date objects as naive dates
                    d = datetime.combine(message.occurs_until, datetime.min.time())
                    until = timezone.make_aware(d, timezone.get_default_timezone())
                else:
                    # otherwise we generate them for a month
                    until = now+relativedelta(months=+1)

                occurrences = list(rrule(WEEKLY,
                                        byweekday=message.eventdate.weekday(),
                                        byhour=message.eventdate.hour,
                                        byminute=message.eventdate.minute,
                                        bysecond=message.eventdate.second,
                                        dtstart=now,
                                        until=until))
                # create events
                for occurrence in occurrences:
                    # we only add the occurence if its date is not the same as the original event
                    # otherwise we get 2 identical events on the same day
                    if occurrence.date() == message.eventdate.date():
                        continue
                    m = deepcopy(message)
                    m.eventdate = occurrence
                    events.append(m)
                    
        # filter out-of-date events+occurences
        events = [e for e in events if e.eventdate >= now]

        # order messages by increasing eventdate
        events = sorted(events, key=operator.attrgetter('eventdate'))

        return events


class NotificationEngine(object):

    def __init__(self, account=None, verbose=False):
        self.account = account
        self.verbose = verbose

    def get(self):
        count = 0
        results = []

        # 1. Private Messages
        # ------------------------------------------------
        # member who have sent you private messages in the last 7 days
        privates = Message.objects.filter(visibility=Message.PRIVATE, 
                                          recipient=self.account,
                                          timestamp__gte=timezone.now()-timedelta(7))\
                                  .order_by('-timestamp')
        if privates.count():
            count += privates.count()
            results.append({
                'type': 'messages',
                'timestamp': privates[0].timestamp,
                'age': privates[0].get_age(),
                'count': privates.count()
            })

        # 2. Events of the day you're in
        # ------------------------------------------------
        # @TODO 'in' events
        events = SearchEngine(account=self.account).search_events()
        events = [r for r in events if r.eventdate is not None and r.eventdate.date() == timezone.now().date()]
        count += len(events)
        for event in events:
            evt = event.format(viewer=self.account)
            results.append({
                'type': 'events',
                'timestamp': evt['timestamp'],
                'event': evt
            })

        # 3. Friends requests
        # ------------------------------------------------
        friend_requests = self.account.get_friend_requests().count()
        if friend_requests:
            count += friend_requests
            results.append({
                'type': 'friends_requests',
                'count': friend_requests
            })

        # 4. Messages you were part of in the last 30 days
        # ------------------------------------------------
        # this includes:
        #   - replies to own meassage
        #   - replies to messages I replied to

        # other's replies to own messages
        my_own = [m['id'] for m in Message.objects.filter(member=self.account, is_reply=False).values('id')]
        replies_to_my_own = Q(is_reply=True, reply_to__in=my_own) & ~Q(member=self.account)

        # replies to messages I replied to
        #   - first, find parent messages to which I replied to
        my_replies = Message.objects.filter(member=self.account, is_reply=True)
        parents_replied_to = list(set([r.reply_to.id for r in my_replies]))
        #   - we get notified of replies to this list of parent messages
        replies_to_thread = Q(is_reply=True, reply_to__id__in=parents_replied_to) & ~Q(member=self.account)

        # get messages
        messages = Message.objects.filter(replies_to_my_own | replies_to_thread)\
                                  .filter(timestamp__gte=timezone.now()-timedelta(30))\
                                  .distinct()\
                                  .order_by('-timestamp')

        count += messages.count()

        # group messages by thread
        parents = [] # tracks parent messages used for grouping replies
        threads = [] # holds threads
        for message in messages:
            if message.reply_to.id not in parents:
                # we create a group which will hold all replies
                # to the same parent
                parents.append(message.reply_to.id)
                thread = {
                    'parent': message.reply_to.format(viewer=self.account),
                    'messages': [
                        message.format(viewer=self.account)
                    ]
                }
                threads.append(thread)
            else:
                # we add the message to group already created
                # the group index will be the same as the parent index in 'parents'
                index = parents.index(message.reply_to.id)
                if message.member.id not in [t['member']['id'] for t in threads[index]['messages']]:
                    # we are interested in notifying who replied
                    # if we have the same member replying twice, we ignore it
                    threads[index]['messages'].append(message.format(viewer=self.account))

        # add threads to results
        for thread in threads:
            results.append({
                'type': 'threads',
                'timestamp': thread['messages'][0]['timestamp'],
                'age': thread['messages'][0]['age'],
                'thread': thread
            })
        
        return {
            'count': count,
            'results': results
        }
