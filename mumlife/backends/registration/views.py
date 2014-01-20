from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site

from registration import signals
from registration.models import RegistrationProfile
from registration.views import ActivationView as BaseActivationView
from registration.views import RegistrationView as BaseRegistrationView

from mumlife.forms import SignUpForm


class RegistrationView(BaseRegistrationView):
    """
    Mumlife registration backend.
    Overrides django-registraion/registration.backends.default

    """
    form_class = SignUpForm

    def register(self, request, **cleaned_data):
        """
        Given an email address and password, register a new
        user account, which will initially be inactive.

        """
        username, email = cleaned_data['email'], cleaned_data['email']
        password = cleaned_data['password']
        first_name, last_name = cleaned_data["first_name"], cleaned_data["last_name"]
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email,
                                                                    password, site)

        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        member = new_user.get_profile()
        member.fullname = ' '.join([first_name, last_name])
        member.postcode = cleaned_data["postcode"]
        member.save()
        member.generate_slug()

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.
        
        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_success_url(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        user registration.
        
        """
        return ('registration_complete', (), {})


class ActivationView(BaseActivationView):
    def activate(self, request, activation_key):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.
        
        """
        activated_user = RegistrationProfile.objects.activate_user(activation_key)
        if activated_user:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated_user,
                                        request=request)
        return activated_user

    def get_success_url(self, request, user):
        return ('registration_activation_complete', (), {})
