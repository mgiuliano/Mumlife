import unittest
from datetime import timedelta
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.utils import timezone
from mumlife.models import Member, Message

class ViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        user = User.objects.create_user(username="user@mumlife.co.uk",
                                        email="user@mumlife.co.uk",
                                        password="secure-password")
        cls._member = user.profile
        cls._member.fullname = 'Test User'
        cls._member.postcode = 'SE16 4JX'
        cls._member.save()

        message = Message.objects.create(member=cls._member,
                                         area=cls._member.area,
                                         body='Message')

    def setUp(self):
        self.client.login(username="user@mumlife.co.uk", password="secure-password")

    def tearDown(self):
        self.client.logout()

    def test_home(self):
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_feed(self):
        response = self.client.get('/local/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/local/?search=#hash')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/local/?search=@private')
        self.assertEqual(response.status_code, 200)

    def test_events(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/events/?search=#hash')
        self.assertEqual(response.status_code, 200)

    def test_messages(self):
        response = self.client.get('/messages/')
        self.assertEqual(response.status_code, 200)

    def test_notifications(self):
        response = self.client.get('/notifications/')
        self.assertEqual(response.status_code, 200)

    def test_write(self):
        response = self.client.get('/write')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.get('/post')
        self.assertEqual(response.status_code, 200)

    def test_post_event(self):
        response = self.client.get('/post-event')
        self.assertEqual(response.status_code, 200)

    def test_edit_event(self):
        event = Message.objects.create(member=self._member,
                                       area=self._member.area,
                                       body='Event',
                                       eventdate=timezone.now() + timedelta(7))
        response = self.client.get('/edit-event/{}/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    def test_delete_event(self):
        event = Message.objects.create(member=self._member,
                                       area=self._member.area,
                                       body='Event',
                                       eventdate=timezone.now() + timedelta(7))
        response = self.client.post('/delete-event/{}/'.format(event.id), follow=True)
        self.assertEqual(response.status_code, 200)
        events = Message.objects.all()
        self.assertNotIn(event, events)

    def test_message(self):
        message = Message.objects.create(member=self._member,
                                         area=self._member.area,
                                         body='Message')
        response = self.client.get('/message/{}/'.format(message.id))
        self.assertEqual(response.status_code, 200)

    def test_members(self):
        response = self.client.get('/members/')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)

    def test_profile_edit(self):
        response = self.client.get('/profile/edit')
        self.assertEqual(response.status_code, 200)
