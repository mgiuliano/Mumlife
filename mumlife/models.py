# mumlife/models.py
import logging
import random
import re
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.encoding import force_unicode
from django.utils.html import strip_tags
from django.utils.timesince import timesince
from tagging.fields import TagField
from tagging.models import Tag
from markitup.fields import MarkupField
from mumlife import utils

logger = logging.getLogger('mumlife.models')


class Page(models.Model):
    title = models.CharField(max_length=64, unique=True)
    slug = models.CharField(max_length=64, unique=True)
    body = MarkupField()
    status = models.BooleanField("Publish Status", default=False)

    def __unicode__(self):
        return self.title
    
    @staticmethod
    def REGEX():
        """ Static pages regular expression used by the URL resolver """
        return r'^(?P<page>{})$'.format('|'.join([p['slug'] for p in Page.objects.filter(status=True).values('slug')]))


class Geocode(models.Model):
    code = models.CharField(max_length=125)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __unicode__(self):
        return '{},{}'.format(self.latitude, self.longitude)


class Member(models.Model):
    PENDING = 0
    VERIFIED = 1
    BANNED = 2
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (BANNED, 'Banned'),
    )
    
    IS_MUM = 0
    IS_DAD = 1
    IS_BUMP = 2
    IS_ORGANISER = 3
    GENDER_CHOICES = (
        (IS_MUM, 'Mum'),
        (IS_DAD, 'Dad'),
        (IS_BUMP, 'Bump'),
        (IS_ORGANISER, 'Organiser'),
    )

    user = models.OneToOneField(User, related_name='profile')
    fullname = models.CharField("Full Name", max_length=64)
    slug = models.CharField("Profile Slug", max_length=255, default='', blank=True)
    postcode = models.CharField("Postcode", max_length=8, help_text='Please include the gap (space) between the outward and inward codes')
    gender = models.IntegerField("Gender", choices=GENDER_CHOICES, null=True, blank=True)
    dob = models.DateField("Date of Birth", null=True, blank=True)
    status = models.IntegerField("Verification Status", choices=STATUS_CHOICES, default=PENDING)

    # Optional
    picture = models.ImageField("Picture", upload_to='./member/%Y/%m/%d', null=True, blank=True, \
                                help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 150 x 150 pixels or larger.")
    about = models.TextField("About", null=True, blank=True)
    spouse = models.ForeignKey('self', related_name='partner', null=True, blank=True, help_text="Spouse or Partner")
    interests = TagField("Interests")
    geocode = models.CharField("Geocode", max_length=255, null=True, blank=True)
    units = models.IntegerField("Units", choices=(
        (0, 'Kilometers'),
        (1, 'Miles'),
    ), null=True, blank=True, default=1, help_text="Distance measurement units")
    max_range = models.IntegerField("Maximum Search Distance", default=5, help_text="Maximum range used by the Event Calendar slider")
    friendships = models.ManyToManyField('self', null=True, blank=True, through='Friendships', \
                                         symmetrical=False, related_name='friends_with+')

    def save(self, *args, **kwargs):
        if self.id is not None:
            # The profile is created after user creation,
            # therefore no data will be associated with it then.
            # It only makes sense to process data when it is updated,
            # i.e. when the data is there
            self.set_slug()
            if self.postcode:
                # Make sure the gap is there
                postcode = utils.Extractor(self.postcode.upper()).extract_postcode()
                if postcode:
                    self.postcode = postcode
                self.set_geocode()
            else:
                self.postcode = 'N/A'
        super(Member, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    def get_distance(self, viewer=None):
        if not viewer or not viewer.geocode or not self.geocode:
            return {
                'units': 'N/A',
                'distance': 'N/A',
                'distance-key': 99999999999
            }
        else:
            units = viewer.units
            units_display = 'Km' if units == 0 else viewer.get_units_display()
            member_geocode = self.geocode.split(',')
            viewer_geocode = viewer.geocode.split(',')
            distance = utils.get_distance(float(member_geocode[0]),
                                          float(member_geocode[1]),
                                          float(viewer_geocode[0]),
                                          float(viewer_geocode[1]))
            if round(distance[units], 1) < 0.5:
                units_display = 'kilometer' if units == 0 else units_display[:-1]
                distance_display = 'less than half a {}'.format(units_display.lower())
            elif round(distance[units], 1) <= 1.1:
                units_display = units_display if units == 0 else units_display[:-1]
                distance_display = '{} {}'.format(round(distance[units], 1), units_display.lower())
            else:
                distance_display = '{} {}'.format(round(distance[units], 1), units_display.lower())
            distance_key = distance[units]
        return {
            'units': units_display,
            'distance': distance_display,
            'distance-key': distance_key
        }

    def format(self, viewer=None):
        member = {}
        member['id'] = self.id
        member['is_admin'] = 'Administrators' in [g['name'] for g in self.user.groups.values('name')]
        member['user'] = self.user.id
        member['slug'] = self.slug
        member['name'] = self.get_name(viewer)
        member['age'] = self.age
        member['gender'] = self.get_gender_display()
        # escape about to prevent script attacks
        member['about'] = strip_tags(force_unicode(self.about)) if self.about else ''
        if viewer:
            member['friend_status'] = viewer.check_if_friend(self)
        else:
            member['friend_status'] = False
        member['area'] = self.area
        member['picture'] = self.picture.url if self.picture else ''
        # distance
        member.update(self.get_distance(viewer))
        member['tags'] = self.tags
        member['kids'] = self.get_kids(viewer=viewer)
        return member

    @property
    def name(self):
        return self.get_name()

    def get_name(self, viewer=None):
        if self == viewer:
            return self.fullname
        else:
            try:
                # show lastame initials
                name = self.fullname.split()
                return '{} {}'.format(name[0], 
                                      ''.join(['{}.'.format(n[0].upper()) for n in name[1:]]))
            except IndexError:
                return 'N/A'
    
    @property
    def age(self):
        return utils.get_age(self.dob)

    @property
    def area(self):
        # For UK only, return inward code
        return self.postcode.split()[0]

    @property
    def kids(self):
        return self.kid_set.exclude(visibility=Kid.HIDDEN)

    def get_kids(self, viewer=None):
        kids = []
        for kid in self.kids:
            # hide HIDDEN kids from other members
            if viewer != self and kid.visibility == Kid.HIDDEN:
                continue
            kids.append(kid.format(viewer=viewer))
        return kids

    @property
    def tags(self):
        tags = Tag.objects.get_for_object(self)
        tags = utils.Extractor(','.join([t.name for t in tags])).extract_tags()
        return [{'key': tag[0], 'value': tag[1]} for tag in tags.items()]

    def add_friend(self, member, status):
        friend, created = Friendships.objects.get_or_create(
            from_member=self,
            to_member=member,
            status=status)
        return friend

    def remove_friend(self, member):
        Friendships.objects.filter(
            from_member=self, 
            to_member=member).delete()

    def get_friends(self, status):
        return self.friendships.filter(to_friend__status=status, to_friend__from_member=self)

    def get_friend_requests(self):
        # Requests exclude any request from BLOCKED members
        blocked = [m['id'] for m in self.get_friends(status=Friendships.BLOCKED).values('id')]
        return Friendships.objects.filter(status=Friendships.PENDING, to_member=self)\
                                  .exclude(from_member__id__in=blocked)

    def check_if_friend(self, member):
        try:
            # first, we check if this member has already been requested as a friend
            member_relation = Friendships.objects.get(from_member=self, to_member=member)
            return member_relation.get_status_display()
        except Friendships.DoesNotExist:
            # if no relation exist, it hasn't been requested as a friend.
            # he might have requested self as a friend though, so we lookup any reverse
            # relationship from the member to self
            member_relation = self.get_friend_requests().filter(from_member=member)
            if member_relation:
                return 'Requesting'
            return False

    def set_slug(self):
        if not self.slug:
            # Slug format: hyphenise(fullname)/random(1-999)/(1+count(fullname)/random(1-999)*(1+count(fullname))
            initials = ''.join(['{}.'.format(n[0]) for n in self.fullname.split()])
            hyphenized = re.sub(r'\s\s*', '-', initials.lower())
            count = Member.objects.filter(slug__contains=hyphenized).count()
            slug = '{}/{}/{}/{}'.format(hyphenized, random.randint(1, 999), count+1, (count+1) * random.randint(1, 999))
            self.slug = slug

    def set_geocode(self):
        if not self.geocode or self.geocode == '(0.0, 0.0)':
            try:
                geocode = Geocode.objects.get(code=self.postcode)
            except Geocode.DoesNotExist:
                # If the geocode for this postcode has not yet been stored,
                # fetch it
                try:
                    point = utils.get_postcode_point(self.postcode)
                except:
                    # The function raises an Exception when the API call fails;
                    # when this happens, do nothing
                    logger.error('The Geocode retrieval for the postcode "{}" has failed.'.format(self.postcode))
                    geocode = (0.0, 0.0)
                else:
                    geocode = Geocode.objects.create(code=self.postcode, latitude=point[0], longitude=point[1])
            self.geocode = str(geocode)


def create_member(sender, instance, created, **kwargs):
    # Only create associated Member on creation,
    # also make sure they are not created when used in the TestCase
    if created and not kwargs.get('raw', False):
        member = Member.objects.create(user=instance)
        notifications = Notifications.objects.create(member=member)
post_save.connect(create_member, sender=User)


class Kid(models.Model):
    HIDDEN = 0
    BRACKETS = 1
    FULL = 2
    VISIBILITY_CHOICES = (
        (HIDDEN, 'Hidden'),
        (BRACKETS, 'Show age bracket'),
        (FULL, 'Show exact age'),
    )

    parents = models.ManyToManyField(Member)
    fullname = models.CharField("Full Name", max_length=64)
    gender = models.IntegerField("Gender", choices=(
        (0, 'Daughter'),
        (1, 'Son'),
    ), null=True)
    dob = models.DateField("Date of Birth", null=True)
    visibility = models.IntegerField("Kid Visibility", choices=VISIBILITY_CHOICES, default=BRACKETS)

    def __unicode__(self):
        return self.fullname

    @property
    def name(self):
        return self.__unicode__()

    @property
    def age(self):
        if self.visibility == Kid.BRACKETS:
            return utils.get_age_bracket(self.dob)
        elif self.visibility == Kid.FULL:
            return utils.get_age(self.dob)
        else:
            # This will only happen on admin/edit page
            # as HIDDEN kids are simply not shown
            return '{} ({})'.format(utils.get_age_bracket(self.dob), utils.get_age(self.dob))

    def format(self, viewer=None):
        kid = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields])
        kid['name'] = self.fullname
        kid['gender'] = self.get_gender_display()
        del kid['dob']
        kid['age'] = self.age
        kid['visibility'] = self.get_visibility_display()
        return kid


class Friendships(models.Model):
    PENDING = 0
    APPROVED = 1
    BLOCKED = 2
    STATUSES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (BLOCKED, 'Blocked'),
    )

    from_member = models.ForeignKey(Member, related_name='from_friend')
    to_member = models.ForeignKey(Member, related_name='to_friend')
    status = models.IntegerField(choices=STATUSES)

    def __unicode__(self):
        return u'{} & {} [{}]'.format(self.from_member, self.to_member, self.get_status_display())


class Message(models.Model):
    # Visibility Settings
    PRIVATE = 0
    FRIENDS = 1
    LOCAL   = 2
    GLOBAL  = 3
    VISIBILITY_CHOICES = (
        (PRIVATE,   'Private'),
        (FRIENDS,   'Friends'),
        (LOCAL,     'Local'),
        (GLOBAL,    'Global'),
    )

    # Occurrence Settings
    OCCURS_ONCE     = 0
    OCCURS_WEEKLY   = 1
    OCCURRENCE_CHOICES = (
        (OCCURS_ONCE,   'Once'),
        (OCCURS_WEEKLY, 'Weekly'),
    )

    member = models.ForeignKey(Member)
    area = models.CharField(max_length=4)
    name = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()
    picture = models.ImageField("Picture", upload_to='./posts/%Y/%m/%d', null=True, blank=True, \
                                help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 403 x 403 pixels or larger.")
    location = models.TextField(blank=True, null=True)
    geocode = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    eventdate = models.DateTimeField(null=True, blank=True)
    eventenddate = models.DateTimeField(null=True, blank=True)
    visibility = models.IntegerField(choices=VISIBILITY_CHOICES, default=LOCAL)
    occurrence = models.IntegerField(choices=OCCURRENCE_CHOICES, default=OCCURS_ONCE)
    occurs_until = models.DateField(null=True, blank=True)
    tags = TagField()
    recipient = models.ForeignKey(Member, null=True, blank=True, related_name='sender')
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, related_name='author')

    def __unicode__(self):
        return u'{}'.format(self.body)

    def save(self, *args, **kwargs):
        self.set_geocode()
        super(Message, self).save(*args, **kwargs)

    @property
    def replies(self):
        return Message.objects.filter(is_reply=True, reply_to=self).order_by('timestamp')

    def get_age(self):
        return timesince(self.timestamp, timezone.now())

    def get_replies(self, viewer=None):
        return [message.format(viewer=viewer) for message in self.replies]

    def is_event(self):
        return True if self.eventdate else False
    is_event.boolean = True

    @property
    def postcode(self):
        if not self.location:
            return None
        postcode = utils.Extractor(self.location).extract_postcode()
        if not postcode:
            return None
        return postcode.upper()

    def get_distance(self, viewer=None):
        if not viewer or not viewer.geocode or not self.geocode:
            return {
                'units': 'N/A',
                'distance': 'N/A',
                'distance-key': 99999999999
            }
        else:
            units = viewer.units
            units_display = 'Km' if units == 0 else viewer.get_units_display()
            message_geocode = self.geocode.split(',')
            viewer_geocode = viewer.geocode.split(',')
            distance = utils.get_distance(float(message_geocode[0]),
                                          float(message_geocode[1]),
                                          float(viewer_geocode[0]),
                                          float(viewer_geocode[1]))
            if round(distance[units], 1) <= 1:
                units_display = units_display if units == 0 else units_display.lower()[:-1]
                distance_display = '{} {}'.format(round(distance[units], 1), units_display)
            else:
                distance_display = '{} {}'.format(round(distance[units], 1), units_display.lower())
            distance_key = distance[units]
        return {
            'units': units_display,
            'distance': distance_display,
            'distance-key': distance_key
        }

    def format(self, viewer=None):
        message = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields])
        if not self.name:
            # messages have empty names,
            # in which case we set it to the body text
            message['title'] = self.body
        else:
            message['title'] = self.name
        # escape body to prevent script attacks
        body = strip_tags(force_unicode(self.body))
        # parse body to display hashtag links
        message['body'] = utils.Extractor(body).parse(with_links=False)
        message['body_with_links'] = utils.Extractor(body).parse()
        message['date'] = self.timestamp.strftime('%c')
        message['picture'] = self.picture.url if self.picture else ''
        # format event details
        if self.eventdate:
            # escape location to prevent script attacks
            message['location'] = strip_tags(force_unicode(self.location))
            message['eventdate'] = self.eventdate.strftime('%A, %b %d, %Y')
            message['eventtime'] = self.eventdate.strftime('%H:%M')
            message['eventyear'] = self.eventdate.strftime('%Y')
            message['eventmonth'] = self.eventdate.strftime('%b')
            message['eventday'] = self.eventdate.strftime('%d')
            if self.eventenddate:
                message['eventenddate'] = self.eventenddate.strftime('%A, %b %d, %Y')
                message['eventendtime'] = self.eventenddate.strftime('%H:%M')
            message['postcode'] = self.postcode
            # events are not necessarily in the same area as the author
            # we therefore override it by the event location postcode area
            if self.postcode:
                message['area'] = self.postcode.split()[0]
            # distance
            message.update(self.get_distance(viewer))
        message['age'] = self.get_age()
        message['member'] = self.member.format(viewer=viewer)
        if message.has_key('recipient') and message['recipient']:
            message['recipient'] = message['recipient'].format(viewer=viewer)
        message['visibility'] = self.get_visibility_display().lower()
        if self.is_reply:
            message['reply_to'] = self.reply_to.id
        else:
            message['tags'] = self.get_tags()
            message['tags_item'] = self.get_tags(filter='item')
            message['tags_inline'] = self.get_tags(filter='inline')
            message['replies'] = self.get_replies(viewer=viewer)
        return message

    def get_tags(self, filter=None):
        tags = utils.Extractor(self.tags).extract_tags()
        if filter:
            if filter == 'item':
                # remove inline tags 
                for tag in utils.Extractor(self.body).extract_tags().keys():
                    del tags[tag]
            elif filter == 'inline':
                # inline tags only
                tags = utils.Extractor(self.body).extract_tags()
        return [{'key': tag[0], 'value': tag[1]} for tag in tags.items()]

    def set_geocode(self):
        try:
            postcode = self.postcode
            if not postcode:
                postcode = 'N/A'
            geocode = Geocode.objects.get(code=postcode)
        except Geocode.DoesNotExist:
            # If the geocode for this postcode has not yet been stored,
            # fetch it
            try:
                point = utils.get_postcode_point(postcode)
            except:
                # The function raises an Exception when the API call fails;
                # when this happens, do nothing
                logger.error('The Geocode retrieval for the postcode "{}" has failed.'.format(self.postcode))
                geocode = (0.0, 0.0)
            else:
                geocode = Geocode.objects.create(code=postcode, latitude=point[0], longitude=point[1])
        self.geocode = str(geocode)


class Notifications(models.Model):
    member = models.OneToOneField(Member, related_name='notifications')
    total = models.IntegerField(default=0)
    messages = models.IntegerField(default=0)
    friends_requests = models.IntegerField(default=0)
    events = models.ManyToManyField(Message, related_name='notification_events', blank=True)
    threads = models.ManyToManyField(Message, related_name='notification_threads', blank=True)

    def __unicode__(self):
        return u"{} Message(s), {} Friend(s) Request(s), {} Event(s), {} Thread(s)"\
               .format(self.messages,
                       self.friends_requests,
                       self.events.count(),
                       self.threads.count())

    def count(self):
        return self.messages \
               + self.friends_requests \
               + self.events.count() \
               + self.threads.count()

    def clear(self):
        self.messages = 0
        self.friends_requests = 0
        self.events.clear()
        self.threads.clear()

    def reset(self, data):
        """
        Reset account notifications.
        'data' is the result of the Notification API.

        """
        self.total = data['total']
        self.events.clear()
        self.threads.clear()
        for result in data['results']:
            if result['type'] in ('events', 'threads'):
                # ManyToMany fields
                if result['type'] == 'events':
                    self.events.add(Message.objects.get(pk=result['event']['id']))
                else:
                    for message in result['thread']['messages']:
                        self.threads.add(Message.objects.get(pk=message['id']))
            else:
                setattr(self, result['type'], result['count'])
        self.save()

    class Meta:
        verbose_name_plural = "notifications"
