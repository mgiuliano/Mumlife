# mumlife/admin.py
import logging
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from mumlife.models import Member, Kid, Friendships, Message

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


class MessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'body', 'area', 'member', 'timestamp', 'visibility', 'tags', 'is_reply')
    list_filter = ('area', 'is_reply')
    inlines = (MessageAdminInline,)
    
    def title(self, obj):
        if obj.name:
            return obj.name
        else:
            return obj.body


site = BackOffice()
site.register(User, UserAdmin)
site.register(Member, MemberAdmin)
site.register(Kid, KidAdmin)
site.register(Message, MessageAdmin)
