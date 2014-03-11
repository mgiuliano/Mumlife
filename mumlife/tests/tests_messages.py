import unittest
from django.test import TestCase
from django.contrib.auth.models import User
from mumlife.models import Member, Message, Friendships

class MessagesSearchTest(TestCase):
    """TestCase for Message Search.
    The methos are in mumlife.models.Member

    Test data contains the following members:
        U1: Freya Hum        SE16
        U2: Suzanna Cole     SE16    Friends: U3, U5
        U3: Amanda Poke      SE16    Friends: U2
        U4: Rachel Chatter   SE22
        U5: Sarah Parker     SE22    Friends: U2

    And the following messages:
        M1: Member, U2 - "#se16 @local"
        M2: Member, U2 - "#se16 @global"
        M3: Member, U2 - "#se16 @friends"
        M4: Member, U5 - "#se22 @local"
        M5: Member, U5 - "#se22 @global"
        M6: Member, U5 - "#se22 @friends"
        M7: Member, U5 - "#se22 @private", to U2
        M8: Member, U1 - "#se16 @private", to U5
        
    """

    def _getId(self, object):
        return int(object.id)

    @classmethod
    def setUpClass(cls):
        # create members
        u1 = User.objects.create_user(username="u1@mumlife.co.uk",
                                      email="u1@mumlife.co.uk",
                                      password="secure-password")
        cls.U1 = u1.get_profile()
        cls.U1.fullname = 'Freya Hum'
        cls.U1.postcode = 'SE16 4JX'
        cls.U1.save()
        u2 = User.objects.create_user(username="u2@mumlife.co.uk",
                                      email="u2@mumlife.co.uk",
                                      password="secure-password")
        cls.U2 = u2.get_profile()
        cls.U2.fullname = 'Suzanna Cole'
        cls.U2.postcode = 'SE16 4RA'
        cls.U2.save()
        u3 = User.objects.create_user(username="u3@mumlife.co.uk",
                                      email="u3@mumlife.co.uk",
                                      password="secure-password")
        cls.U3 = u3.get_profile()
        cls.U3.fullname = 'Amanda Poke'
        cls.U3.postcode = 'SE16 6NN'
        cls.U3.save()
        u4 = User.objects.create_user(username="u4@mumlife.co.uk",
                                      email="u4@mumlife.co.uk",
                                      password="secure-password")
        cls.U4 = u4.get_profile()
        cls.U4.fullname = 'Rachel Chatter'
        cls.U4.postcode = 'SE22 0NH'
        cls.U4.save()
        u5 = User.objects.create_user(username="u5@mumlife.co.uk",
                                      email="u5@mumlife.co.uk",
                                      password="secure-password")
        cls.U5 = u5.get_profile()
        cls.U5.fullname = 'Sarah Parker'
        cls.U5.postcode = 'SE22 0HN'
        cls.U5.save()

        # create relationships
        cls.U2.add_friend(cls.U3, status=Friendships.APPROVED)
        cls.U2.add_friend(cls.U5, status=Friendships.APPROVED)
        cls.U3.add_friend(cls.U2, status=Friendships.APPROVED)
        cls.U5.add_friend(cls.U2, status=Friendships.APPROVED)

        # create messages
        cls.M1 = Message.objects.create(member=cls.U2,
                                        area=cls.U2.area, 
                                        body='M1 #se16 @global',
                                        tags='#se16')
        cls.M2 = Message.objects.create(member=cls.U2,
                                        area=cls.U2.area,
                                        body='M2 #se16 @global',
                                        visibility=Message.GLOBAL,
                                        tags='#se16')
        cls.M3 = Message.objects.create(member=cls.U2,
                                        area=cls.U2.area,
                                        body='M3 #se16 @friends',
                                        visibility=Message.FRIENDS,
                                        tags='#se16')
        cls.M4 = Message.objects.create(member=cls.U5,
                                        area=cls.U5.area,
                                        body='M4 #se22 @local',
                                        tags='#se22')
        cls.M5 = Message.objects.create(member=cls.U5,
                                        area=cls.U5.area,
                                        body='M5 #se22 @global',
                                        visibility=Message.GLOBAL,
                                        tags='#se22')
        cls.M6 = Message.objects.create(member=cls.U5,
                                        area=cls.U5.area,
                                        body='M6 #se22 @friends',
                                        visibility=Message.FRIENDS,
                                        tags='#se22')
        cls.M7 = Message.objects.create(member=cls.U5,
                                        area=cls.U5.area,
                                        body='M7 #se22 @private',
                                        visibility=Message.PRIVATE,
                                        recipient=cls.U2,
                                        tags='#se22')
        cls.M8 = Message.objects.create(member=cls.U1,
                                        area=cls.U1.area,
                                        body='M8 #se16 @private',
                                        visibility=Message.PRIVATE,
                                        recipient=cls.U5,
                                        tags='#se16')

    def test_U1(self):
        """Tests that U1 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (GLOBAL, my area)
            S2 "@global"        : M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (GLOBAL, my area)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : No Match
            S7 "@private"       : M8 (PRIVATE to U5)

        """
        searches = [
            ("@local",          [1,2]),
            ("@global",         [5]),
            ("#se16",           [1,2]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        []),
            ("@private",        [8]),
        ]
        for terms, expected in searches:
            messages = self.U1.get_messages(search=terms)
            self.assertQuerysetEqual(messages, expected, self._getId, ordered=False)

    def test_U2(self):
        """ Tests that U2 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (LOCAL)
            S2 "@global"        : M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (LOCAL)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : M3 (OWN, FRIEND), M4 (Friend), M5 (Friend), M6 (Friend)
            S7 "@private"       : M7 (PRIVATE from U5)

        """
        searches = [
            ("@local",          [1,2]),
            ("@global",         [5]),
            ("#se16",           [1,2]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        [3,4,5,6]),
            ("@private",        [7]),
        ]
        for terms, expected in searches:
            messages = self.U2.get_messages(terms)
            self.assertQuerysetEqual(messages, expected, self._getId, ordered=False)

    def test_U3(self):
        """Tests that U3 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (GLOBAL, my area), M3 (FRIEND, my area)
            S2 "@global"        : M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (GLOBAL, my area), M3 (FRIEND, my area)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : M1 (Friend), M2 (Friend), M3 (Friend) 
            S7 "@private"       : No Match

        """
        searches = [
            ("@local",          [1,2,3]),
            ("@global",         [5]),
            ("#se16",           [1,2,3]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        [1,2,3]),
            ("@private",        []),
        ]
        for terms, expected in searches:
            messages = self.U3.get_messages(terms)
            self.assertQuerysetEqual(messages, expected, self._getId, ordered=False)

    def test_U4(self):
        """Tests that U4 sees, for the followng searches:
            S1 "@local"         : M4 (LOCAL), M5 (GLOBAL, my area)
            S2 "@global"        : M2 (GLOBAL, outside area)
            S3 "#se16"          : No Match
            S4 "#se22"          : M4 (LOCAL), M5 (GLOBAL, my area)
            S5 "#se22 @global"  : No Match
            S6 "@friend"        : No Match
            S7 "@private"       : No Match 

        """
        searches = [
            ("@local",          [4,5]),
            ("@global",         [2]),
            ("#se16",           []),
            ("#se22",           [4,5]),
            ("#se22 @global",   []),
            ("@friends",        []),
            ("@private",        []),
        ]
        for terms, expected in searches:
            messages = self.U4.get_messages(terms)
            self.assertQuerysetEqual(messages, expected, self._getId, ordered=False)

    def test_U5(self):
        """Tests that U5 sees, for the followng searches:
            S1 "@local"         : M4 (LOCAL), M5 (LOCAL)
            S2 "@global"        : M2 (GLOBAL, outside area)
            S3 "#se16"          : No Match
            S4 "#se22"          : M4 (LOCAL), M5 (LOCAL)
            S5 "#se22 @global"  : No Match
            S6 "@friend"        : M1 (Friend), M2 (Friend), M3 (Friend), M6 (OWN, FRIENDS)
            S7 "@private"       : M7 (PRIVATE to U2), M8 (PRIVATE from U1)

        """
        searches = [
            ("@local",          [4,5]),
            ("@global",         [2]),
            ("#se16",           []),
            ("#se22",           [4,5]),
            ("#se22 @global",   []),
            ("@friends",        [1,2,3,6]),
            ("@private",        [7,8]),
        ]
        for terms, expected in searches:
            messages = self.U5.get_messages(terms)
            self.assertQuerysetEqual(messages, expected, self._getId, ordered=False)
