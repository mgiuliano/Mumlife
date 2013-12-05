# mumlife/engines.py
import logging
import operator
import re
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from tagging.models import Tag, TaggedItem
from mumlife import utils
from mumlife.models import Message, Friendships

logger = logging.getLogger('mumlife.engines')


class SearchEngine(object):
    def __init__(self, account=None, verbose=False):
        self.account = account
        self.verbose = verbose
    
    def search(self, terms='@local'):
        """
        Search rules:
            - search terms are matches against hashtags;
            - search for nothing returns local results;
            - @local (default) includes:
                - LOCAL & GLOBAL messages within account area
                - FRIENDS messages within account area, from account friends
                (using @local is redundant, as it is the default);
            - @global includes:
                - same as @local, plus
                - GLOBAL messages outside account area;
            - @friends includes:
                - FRIENDS messages in all areas, from account friends
            - @private includes:
                - PRIVATE messages sent to account, regardless of area or friendship

        """
        # whitespaces are not allowed, so get rid of them
        tagstring = re.sub(r'\s\s*', '', terms)
        if not tagstring:
            tagstring = '@local' # default search

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

        # extract flags @flags
        # only one flag is allowed. Exceptions will default to @local
        flags = utils.Extractor(tagstring).extract_flags()
        if not flags or len(flags) > 1:
            flags = ['@local']
        flag = flags[0]

        # @friends results
        if flag == '@friends':
            # OWN FRIENDS messages
            _own = Q(member=self.account, visibility=Message.FRIENDS)
            if self.verbose:
                print ' ... Own >>>', messages.filter(_own)
            # All messages from account friends
            _friends = Q(member__friendships__to_friend__status=Friendships.APPROVED,
                         member__friendships__to_friend__to_member=self.account) \
                       & Q(visibility__in=[Message.LOCAL, Message.GLOBAL, Message.FRIENDS])
            if self.verbose:
                print ' ... Friends >>>', messages.filter(_friends)
            messages = messages.filter(_own | _friends)

        # @private results
        elif flag == '@private':
            # OWN PRIVATE messages
            _own = Q(member=self.account, visibility=Message.PRIVATE)
            if self.verbose:
                print ' ... Own >>>', messages.filter(_own)
            # PRIVATE messages sent to account, regardless of area
            _privates = Q(visibility=Message.PRIVATE, recipient=self.account)
            if self.verbose:
                print ' ... Privates >>>', messages.filter(_privates)
            messages = messages.filter(_own | _privates)

        # @local & @global results
        else:
            # LOCAL & GLOBAL messages within account area
            _locals = Q(visibility__in=[Message.LOCAL, Message.GLOBAL], area=self.account.area)
            if self.verbose:
                print ' ... Locals >>>', messages.filter(_locals)
            # FRIENDS messages within account area, from account friends
            _friends = Q(member__friendships__to_friend__status=Friendships.APPROVED,
                         member__friendships__to_friend__to_member=self.account) \
                       & Q(visibility=Message.FRIENDS) \
                       & Q(area=self.account.area)
            if self.verbose:
                print ' ... Friends >>>', messages.filter(_friends)

            # @global results only
            if flag == '@global':
                # GLOBAL messages outside account area
                _globals = Q(visibility=Message.GLOBAL) & ~Q(area=self.account.area)
                if self.verbose:
                    print ' ... Globals >>>', messages.filter(_globals)
                messages = messages.filter(_locals | _globals | _friends)

            # @local results only
            else:
                messages = messages.filter(_locals | _friends)

        # order messages in reverse chronological order
        messages = messages.order_by('-timestamp')
        
        return messages.distinct()


class NotificationEngine(object):

    def __init__(self, account=None, verbose=False):
        self.account = account
        self.verbose = verbose

    def get(self):
        results = {}

        # 1. Messages you were part of in the last 7 days
        # -----------------------------------------------
        # this includes:
        #   - replies to own meassage
        #   - replies to messages I replied to
        pool = Message.objects.filter(timestamp__gte=timezone.now()-timedelta(7))\
                              .order_by('-timestamp')

        # replies to own messages
        replies_to_own = Q(reply_to__member=self.account) & ~Q(is_reply=False, member=self.account)

        # replies to messages I replied to
        #   - first, find parent messages to which I replied to
        replies = [m['id'] for m in Message.objects.filter(is_reply=True, member=self.account).values('id')]
        parent_messages = [m['id'] for m in Message.objects.filter(is_reply=False).exclude(member=self.account).values('id')]
        #   - we get notified of replies to this list of parent messages
        replies_to_thread = Q(is_reply=True, reply_to__id__in=parent_messages) & ~Q(member=self.account)

        # union
        messages = pool.filter(replies_to_own | replies_to_thread)

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
                # the group index will be the same as the group length - 1
                # i.e. length = 2, index = 1
                if message.member.id not in [t['member']['id'] for t in threads[len(threads)-1]['messages']]:
                    # we are interested in notifying who replied
                    # if we have the same member replying twice, we ignore it
                    threads[len(threads)-1]['messages'].append(message.format(self.account))
        results['replies'] = threads
        
        # 2. Private messages


        return results
