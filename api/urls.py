from django.conf.urls import patterns, include, url
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import MemberListView, MemberView, \
                      KidListView, KidView, \
                      FriendshipsListView, FriendshipView, \
                      MessageListView, MessageView, MessagePostView, \
                      NotificationListView

urlpatterns = patterns('',

    url(r'^$', 'api.views.api_root'),
    url(r'^members/$', MemberListView.as_view(), name='members-list'),
    url(r'^members/(?P<pk>[0-9]+)/$', MemberView.as_view(), name='member-detail'),
    url(r'^kids/$', KidListView.as_view(), name='kids-list'),
    url(r'^kids/(?P<pk>[0-9]+)/$', KidView.as_view(), name='kid-detail'),
    url(r'^friendships/$', FriendshipsListView.as_view(), name='friendships-list'),
    url(r'^friendships/(?P<pk>[0-9]+)/$', FriendshipView.as_view(), name='friendship-view'),
    url(r'^messages/(?P<page>\d*)/?(?P<terms>.*)$', MessageListView.as_view(), name='messages-list'),
    url(r'^message/(?P<pk>[0-9]+)/$', MessageView.as_view(), name='message-detail'),
    url(r'^message/post$', MessagePostView.as_view(), name='message-add'),
    url(r'^notifications/$', NotificationListView.as_view(), name='notifications-list'),

    # include login URLs for the browseable API.
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),

)

urlpatterns = format_suffix_patterns(urlpatterns)
