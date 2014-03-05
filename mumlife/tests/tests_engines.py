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
        self.m1 = self.u1.get_profile()
        self.m1.postcode = 'SE16 4JX'
        self.m1.save()
        self.u2 = User.objects.create_user(username="m2@mumlife.co.uk",
                                           email="m2@beatscope.co.uk",
                                           password="secure-password")
        self.m2 = self.u2.get_profile()
        self.m2.postcode = 'SE16 5XH'
        self.m2.save()
        self.u3 = User.objects.create_user(username="m3@mumlife.co.uk",
                                           email="m3@beatscope.co.uk",
                                           password="secure-password")
        self.m3 = self.u3.get_profile()
        self.m3.postcode = 'SE22 0NH'
        self.m3.save()

    def test_postcode_areas(self):
        self.assertEqual(self.m1.area, 'SE16')
        self.assertEqual(self.m2.area, 'SE16')
        self.assertEqual(self.m3.area, 'SE22')

    #@unittest.skip('Depends on Bing Maps API')
    #def test_postcode_distance(self):
    #    distance_1_2 = self.m1.get_distance_from(self.m2)
    #    distance_1_3 = self.m1.get_distance_from(self.m3)
    #    distance_2_3 = self.m2.get_distance_from(self.m3)
    #    self.assertEqual(distance_1_2, {'units': u'Mile', 'distance-display': '0.8 mile', 'distance': 0.7857321953541907})
    #    self.assertEqual(distance_1_3, {'units': u'Miles', 'distance-display': '3.4 miles', 'distance': 3.365372382212894})
    #    self.assertEqual(distance_2_3, {'units': u'Miles', 'distance-display': '3.9 miles', 'distance': 3.8686050934826786})
