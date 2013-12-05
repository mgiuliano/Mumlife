# mumlife/models.py
import logging
import random
import re
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timesince import timesince
from tagging.fields import TagField
from tagging.models import Tag
from mumlife import utils

logger = logging.getLogger('mumlife.models')


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

    user = models.OneToOneField(User, related_name='profile')
    fullname = models.CharField("Full Name", max_length=64)
    slug = models.CharField("Profile Slug", max_length=255, null=True, blank=True)
    postcode = models.CharField("Postcode", max_length=8, help_text='Please include the gap (space) between the outward and inward codes')
    gender = models.IntegerField("Gender", choices=(
        (0, 'Female'),
        (1, 'Male'),
    ), null=True)
    dob = models.DateField("Date of Birth", null=True, help_text="Format 'YYYY-MM-DD' (e.g. 1976-04-27)")
    status = models.IntegerField("Verification Status", choices=STATUS_CHOICES, default=PENDING)

    # Optional
    picture = models.ImageField("Picture", upload_to='./member/%Y/%m/%d', null=True, blank=True, \
                                help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 90 x 90 pixels or larger.")
    about = models.TextField("About", null=True, blank=True)
    spouse = models.ForeignKey('self', related_name='partner', null=True, blank=True, help_text="Spouse or Partner")
    interests = TagField("Interests")
    units = models.IntegerField("Units", choices=(
        (0, 'Kilometers'),
        (1, 'Miles'),
    ), null=True, default=1, help_text="Distance measurement units")
    friendships = models.ManyToManyField('self', null=True, blank=True, through='Friendships', \
                                         symmetrical=False, related_name='friends_with+')

    def __unicode__(self):
        return self.name

    def format(self, viewer=None):
        member = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields])
        member['user'] = self.user.id
        member['name'] = self.get_name(viewer)
        member['dob'] = self.dob.strftime('%c')
        member['age'] = self.age
        member['gender'] = self.get_gender_display()
        if viewer:
            member['friend_status'] = viewer.check_if_friend(self)
        else:
            member['friend_status'] = False
        member['area'] = self.area
        member['picture'] = self.picture.url if self.picture else ''
        if not viewer or (not self.geocode.latitude and not self.geocode.longitude):
            member['units'] = viewer.get_units_display()
            member['distance'] = 'N/A'
            member['distance-key'] = 99999999999
        else:
            distance = utils.get_distance(self.geocode.latitude,
                                          self.geocode.longitude,
                                          viewer.geocode.latitude,
                                          viewer.geocode.longitude)
            if distance[viewer.units] < 0.5:
                member['distance'] = 'less than half a {}'.format(viewer.get_units_display().lower()[:-1])
            elif distance[viewer.units] <= 1:
                member['distance'] = '{} {}'.format(round(distance[viewer.units], 1), viewer.get_units_display().lower()[:-1])
            else:
                member['distance'] = '{} {}'.format(round(distance[viewer.units], 1), viewer.get_units_display().lower())
            member['distance-key'] = distance[viewer.units]
        member['tags'] = self.tags
        member['kids'] = self.get_kids(viewer=viewer)
        return member

    @property
    def name(self):
        return self.get_name()

    def get_name(self, viewer=None):
        if self == viewer:
            return 'Me'
        if not viewer or not self.check_if_friend(viewer) == 'Approved':
            # Hide lastname for non-friends
            name = self.fullname.split(r' ')
            return '{} {}'.format(name[0], ''.join(['{}'.format(n[0].upper()) for n in name[1:]]))
        return self.fullname
    
    @property
    def age(self):
        return utils.get_age(self.dob)

    @property
    def area(self):
        # For UK only, return inward code
        return self.postcode.split(' ')[0]

    @property
    def kids(self):
        return self.kid_set.exclude(visibility=Kid.HIDDEN)

    def get_kids(self, viewer=None):
        if not viewer or not self.check_if_friend(viewer) == 'Approved':
            # Hide kids from non-friends
            return []
        return [kid.format(viewer=viewer) for kid in self.kids]

    @property
    def tags(self):
        tags = Tag.objects.get_for_object(self)
        tags = utils.Extractor(','.join([t.name for t in tags])).extract_tags()
        return [{'key': tag[0], 'value': tag[1]} for tag in tags.items()]

    @property
    def geocode(self):
        try:
            geocode = Geocode.objects.get(code=self.postcode)
        except Geocode.DoesNotExist:
            # If the geocode for this postcode has not yet been stored,
            # fetch it
            try:
                point = utils.get_postcode_point(self.postcode)
            except:
                # The function raises an Exception when the postcode does not exist
                # we store the resulst as (0, 0) to avoid fetching the API every time
                point = (0.0, 0.0)
            geocode = Geocode.objects.create(code=self.postcode, latitude=point[0], longitude=point[1])
        return geocode

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
        return Friendships.objects.filter(status=Friendships.PENDING, to_member=self)

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

    def generate_slug(self):
        if not self.slug:
            # Slug format: hyphenise(fullname)/random(1-999)/(1+count(fullname)/random(1-999)*(1+count(fullname))
            initials = ''.join(['{}.'.format(n[0]) for n in self.fullname.split(r' ')])
            hyphenized = re.sub(r'\s\s*', '-', initials.lower())
            count = Member.objects.filter(slug__contains=hyphenized).count()
            slug = '{}/{}/{}/{}'.format(hyphenized, random.randint(1, 999), count+1, (count+1) * random.randint(1, 999))
            self.slug = slug
            self.save()

def create_member(sender, instance, created, **kwargs):
    # Only create associated Member on creation,
    # also make sure they are not created when used in the TestCase
    if created and not kwargs.get('raw', False):
        member = Member.objects.create(user=instance)
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
    dob = models.DateField("Date of Birth", null=True, help_text="Format 'YYYY-MM-DD' (e.g. 2012-09-05)")
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


class Message(models.Model):
    PRIVATE = 0
    FRIENDS = 1
    LOCAL = 2
    GLOBAL = 3
    VISIBILITY_CHOICES = (
        (PRIVATE, 'Private'),
        (FRIENDS, 'Friends'),
        (LOCAL, 'Local'),
        (GLOBAL, 'Global'),
    )

    member = models.ForeignKey(Member)
    area = models.CharField(max_length=4)
    name = models.CharField(max_length=200, blank=True, null=True)
    body = models.TextField()
    location = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    eventdate = models.DateTimeField(null=True, blank=True)
    visibility = models.IntegerField(choices=VISIBILITY_CHOICES, default=LOCAL)
    tags = TagField()
    recipient = models.ForeignKey(Member, null=True, blank=True, related_name='sender')
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, related_name='author')

    def __unicode__(self):
        return '{}: {}...'.format(str(self.member), self.body[:60])

    @property
    def replies(self):
        return Message.objects.filter(is_reply=True, reply_to=self).order_by('timestamp')

    def get_age(self):
        return timesince(self.timestamp, timezone.now())

    def get_replies(self, viewer=None):
        return [message.format(viewer=viewer) for message in self.replies]

    @property
    def postcode(self):
        if not self.location:
            return None
        postcode = utils.Extractor(self.location).extract_postcode()
        if not postcode:
            return None
        return postcode

    @property
    def geocode(self):
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
                # The function raises an Exception when the postcode does not exist
                # we store the resulst as (0, 0) to avoid fetching the API every time
                point = (0.0, 0.0)
            geocode = Geocode.objects.create(code=postcode, latitude=point[0], longitude=point[1])
        return geocode

    def format(self, viewer=None):
        message = dict([(f.name, getattr(self, f.name)) for f in self._meta.fields])
        if not self.name:
            # messages have empty names,
            # in which case we set it to the body text
            message['title'] = self.body
        else:
            message['title'] = self.name
        # parse body to display hashtag links
        message['body'] = utils.Extractor(self.body).parse(with_links=False)
        message['body_with_links'] = utils.Extractor(self.body).parse()
        message['timestamp'] = self.timestamp.strftime('%c')
        # format event details
        if self.eventdate:
            message['eventdate'] = self.eventdate.strftime('%A, %b %d')
            message['eventtime'] = self.eventdate.strftime('%H:%M')
            message['eventmonth'] = self.eventdate.strftime('%b')
            message['eventday'] = self.eventdate.strftime('%d')
            message['postcode'] = self.postcode
            # distance details
            if not viewer or (not self.geocode.latitude and not self.geocode.longitude):
                message['units'] = viewer.get_units_display()
                message['distance'] = 'N/A'
                message['distance-key'] = 99999999999
            else:
                distance = utils.get_distance(self.geocode.latitude,
                                              self.geocode.longitude,
                                              viewer.geocode.latitude,
                                              viewer.geocode.longitude)
                if distance[viewer.units] <= 1:
                    message['distance'] = '{} {}'.format(round(distance[viewer.units], 1), viewer.get_units_display().lower()[:-1])
                else:
                    message['distance'] = '{} {}'.format(round(distance[viewer.units], 1), viewer.get_units_display().lower())
                message['distance-key'] = distance[viewer.units]
        message['age'] = self.get_age()
        message['member'] = self.member.format(viewer=viewer)
        message['visibility'] = self.get_visibility_display().lower()
        if self.is_reply:
            message['reply_to'] = self.reply_to.id
        else:
            message['tags'] = self.get_tags()
            message['replies'] = self.get_replies(viewer=viewer)
        return message

    def get_tags(self):
        tags = utils.Extractor(self.tags).extract_tags()
        # remove any inline tag from the list of tags, 
        # so they don't appear twise
        for tag in utils.Extractor(self.body).extract_tags().keys():
            del tags[tag]
        return [{'key': tag[0], 'value': tag[1]} for tag in tags.items()]
