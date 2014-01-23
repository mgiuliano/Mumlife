# mumlife/admin.py
import logging
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.models import Site
from django.utils import timezone
from mumlife.models import Member, Kid, Friendships, Message, Notifications, Geocode

logger = logging.getLogger('mumlife.admin')


class BackOffice(admin.sites.AdminSite):
    pass


class UserAdmin(UserAdmin):
    list_display = ('name', 'postcode', 'email', 'status', 'is_staff')

    def name(self, obj):
        if obj.profile.fullname:
            return obj.profile.fullname
        else:
            return obj.username

    def postcode(self, obj):
        return obj.profile.postcode

    def status(self, obj):
        return obj.profile.get_status_display()


class KidAdminInline(admin.TabularInline):
    model = Kid.parents.through
    extra = 0

class FriendAdminInline(admin.StackedInline):
    model = Friendships
    fk_name = 'from_member'
    extra = 0

class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'postcode', 'geocode', 'kids', 'friends', 'friend_requests', 'interests', 'status')
    list_editable = ('postcode', 'interests', 'status')
    list_filter = ('status',)
    search_fields = ('fullname', 'user__email')
    inlines = (KidAdminInline, FriendAdminInline)

    def name(self, obj):
        if obj.fullname:
            return obj.fullname
        else:
            return obj.user.username

    def friends(self, obj):
        return obj.get_friends(Friendships.APPROVED).count()

    def friend_requests(self, obj):
        return obj.get_friend_requests().count()

    def kids(self, obj):
        return obj.kid_set.count()


class KidAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'visibility', 'parent')
    fields = ('fullname', 'gender', 'dob', 'visibility')
    inlines = (KidAdminInline,)
    
    def parent(self, obj):
        return ', '.join([str(p) for p in obj.parents.all()])
    

class MessageAdminInline(admin.StackedInline):
    model = Message
    fields = ('member',)
    extra = 0


class MessageIsEventListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'is event'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'isevent'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() in ('yes', 'no'):
            now = timezone.now()
            if self.value() == 'yes':
                return queryset.filter(eventdate__isnull=False)
            else:
                return queryset.exclude(eventdate__isnull=False)
        return queryset


class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'area', 'postcode', 'member', 'timestamp', 'visibility', 'eventdate', 'tags', 'is_reply', 'is_event')
    list_filter = ('area', 'is_reply', MessageIsEventListFilter)
    search_fields = ('name', 'body', 'tags')
    inlines = (MessageAdminInline,)
    
    def title(self, obj):
        if obj.name:
            return obj.name
        else:
            return obj

    def is_event(self, obj):
        if obj.eventdate:
            return True
        return False


class NotificationsAdmin(admin.ModelAdmin):
    list_display = ('member', '__unicode__', 'total')


class GeocodeAdmin(admin.ModelAdmin):
    list_display = ('code', '__unicode__')
    search_fields = ('code',)
    

site = BackOffice()
site.register(Site)
site.register(User, UserAdmin)
site.register(Member, MemberAdmin)
site.register(Kid, KidAdmin)
site.register(Message, MessageAdmin)
site.register(Notifications, NotificationsAdmin)
site.register(Geocode, GeocodeAdmin)
