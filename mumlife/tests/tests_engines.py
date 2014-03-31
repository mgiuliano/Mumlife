import logging
import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from mumlife.models import Member, Message

logger = logging.getLogger('mumlife.tests')


class MemberTest(TestCase):
    """TestCase for Member Model"""
    def setUp(self):
        self.u1 = User.objects.create_user(username="m1@mumlife.co.uk",
                                           email="m1@beatscope.co.uk",
                                           password="secure-password")
        self.m1 = self.u1.profile
        self.m1.postcode = 'SE16 4JX'
        self.m1.save()
        self.u2 = User.objects.create_user(username="m2@mumlife.co.uk",
                                           email="m2@beatscope.co.uk",
                                           password="secure-password")
        self.m2 = self.u2.profile
        self.m2.postcode = 'SE16 5XH'
        self.m2.save()
        self.u3 = User.objects.create_user(username="m3@mumlife.co.uk",
                                           email="m3@beatscope.co.uk",
                                           password="secure-password")
        self.m3 = self.u3.profile
        self.m3.postcode = 'SE22 0NH'
        self.m3.save()

    def test_postcode_areas(self):
        self.assertEqual(self.m1.area, 'SE16')
        self.assertEqual(self.m2.area, 'SE16')
        self.assertEqual(self.m3.area, 'SE22')
