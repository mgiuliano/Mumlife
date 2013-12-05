# mumlife/urls.py
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.auth.decorators import login_required
from mumlife.admin import site
from mumlife.uploads import FileUploader
#from mumlife.forms import PassResetForm

urlpatterns = patterns('',

    url(r'^$', 'mumlife.views.home'),
    url(r'^s/(?P<tagstring>.*)', 'mumlife.views.search'),
    url(r'^events/(?P<tagstring>.*)', 'mumlife.views.events'),
    url(r'^notifications', 'mumlife.views.notifications'),

    url(r'^write-message$', 'mumlife.views.write_message'),
    url(r'^create-event$', 'mumlife.views.create_event'),
    url(r'^edit-event/(?P<event_id>[0-9]+)$$', 'mumlife.views.edit_event'),

    url(r'^message/(?P<mid>[0-9]+)$', 'mumlife.views.message'),
    url(r'^members/(?P<tagstring>.*)', 'mumlife.views.members'),
    url(r'^members$', 'mumlife.views.members'),

    # Member Pages
    #url(r'^member/sign-up$', 'nirit.views.sign_up'),
    #url(r'^member/sign-up/complete$', 'nirit.views.sign_up_complete'),
    #url(r'^member/sign-up/activation-required$', 'nirit.views.sign_up_activation_required'),
    #url(r'^member/sign-up/activate$', 'nirit.views.sign_up_activate'),

    url(r'^member/password/reset/$', 'django.contrib.auth.views.password_reset',
        {
            'from_email': settings.EMAIL_FROM,
            #'password_reset_form': PassResetForm,
            'post_reset_redirect' : '/member/password/reset/done/'
        },
        name="password_reset"),
    url(r'^member/password/reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    url(r'^member/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',
        {
            'post_reset_redirect' : '/member/password/reset/complete/'
        }),
    url(r'^member/password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete'),
    url(r'^member/password/change/', 'django.contrib.auth.views.password_change',
        {
            'post_change_redirect': '/profile/edit/account'
        }),

    url(r'^upload$', login_required(FileUploader())),
    url(r'^profile/edit$', 'mumlife.views.profile_edit'),
    url(r'^profile/edit/account$', 'mumlife.views.profile_edit', {'section': 'account'}),
    url(r'^profile/edit/kids$', 'mumlife.views.profile_edit', {'section': 'kids'}),
    url(r'^profile/edit/kids/(?P<kid>[0-9]+)$', 'mumlife.views.profile_edit', {'section': 'kid'}),
    url(r'^profile/edit/interests$', 'mumlife.views.profile_edit', {'section': 'interests'}),
    url(r'^profile/edit/preferences$', 'mumlife.views.profile_edit', {'section': 'preferences'}),
    url(r'^profile$', 'mumlife.views.profile'),
    url(r'^profile/(?P<slug>.+)$', 'mumlife.views.profile'),
    url(r'^logout', 'django.contrib.auth.views.logout_then_login'),

    # Include URLs for the REST API (v1).
    url(r'^1/', include('api.urls')),

    # Back Office
    url(r'^back-office/', include(site.urls)),

)
