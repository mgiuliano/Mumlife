# mumlife/forms.py
import logging
from django import forms
from django.contrib.auth.forms import PasswordResetForm
#from django.contrib.auth.tokens import default_token_generator
from mumlife.models import Member, Kid, Message
from mumlife.widgets import ImageWidget

logger = logging.getLogger('mumlife.forms')

#class PassResetForm(PasswordResetForm):
#    """
#    Override PasswordResetForm,
#    to allow email sent to use HTML format.
#
#    """
#    def save(self, domain_override=None,
#             subject_template_name='registration/password_reset_subject.txt',
#             email_template_name='registration/password_reset_email.html',
#             use_https=False, token_generator=default_token_generator,
#             from_email=None, request=None):
#        """
#        Generates a one-use only link for resetting password and sends to the
#        user.
#        """
#        for user in self.users_cache:
#            if not domain_override:
#                current_site = get_current_site(request)
#                site_name = current_site.name
#                domain = current_site.domain
#            else:
#                site_name = domain = domain_override
#            c = {
#                'email': user.email,
#                'domain': domain,
#                'site_name': site_name,
#                'uid': int_to_base36(user.pk),
#                'user': user,
#                'token': token_generator.make_token(user),
#                'protocol': use_https and 'https' or 'http',
#            }
#            subject = loader.render_to_string('emails/password_reset_subject.txt', c)
#            # Email subject *must not* contain newlines
#            subject = ''.join(subject.splitlines())
#            text_content = loader.render_to_string('emails/password_reset.txt', c)
#            html_content = loader.render_to_string('emails/password_reset.html', c)
#            msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
#            msg.attach_alternative(html_content, "text/html")
#            msg.send()


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('fullname', 'postcode', 'gender', 'dob', 'picture', 'about', 'interests', 'units')
        widgets = {
            'picture': ImageWidget(),
            'gender': forms.RadioSelect
        }


class KidForm(forms.ModelForm):
    class Meta:
        model = Kid
        fields = ('fullname', 'gender', 'dob', 'visibility')

class MessageForm(forms.ModelForm):
    VISIBILITY = tuple([o for o in Message.VISIBILITY_CHOICES if o[0] != Message.PRIVATE])

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['visibility'].choices = self.VISIBILITY
        self.fields['visibility'].initial = Message.LOCAL

    class Meta:
        model = Message
        widgets = {
            'body': forms.Textarea(attrs={
                'data-name': 'Message',
                'class': 'message-body elastic',
                'rows': "2",
                'cols': "70",
                'required': "required",
            }),
            'visibility': forms.Select(attrs={
                'class': "message-visibility hidden"
            }),
            'name': forms.TextInput(attrs={
                'data-name': "Event Name",
                'class': "message-name",
                'size': "200",
                'placeholder': "Event name",
                'required': "required"
            }),
            'location': forms.Textarea(attrs={
                'data-name': "Address &amp; Postcode",
                'class': "message-location elastic",
                'rows': "2",
                'cols': "70",
                'required': "required"
            })
        }
