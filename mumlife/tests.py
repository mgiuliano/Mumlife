from django.test import TestCase
from django.contrib.auth.models import User
from mumlife.models import Member, Message
from mumlife.engines import SearchEngine

class SearchEngineTest(TestCase):
    """
    TestCase for SearchEngine class.

    Test data has been dumped excluding ContentType:
    ./manage.py dumpdata --indent=4 --natural -e contenttypes > mumlife/fixtures/testdata.json

    The test data contains the following members:
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
    fixtures = ['testdata.json']

    def getId(self, object):
        return int(object.id)

    def setUp(self):
        # Delete superuser
        Member.objects.filter(user__is_superuser=1).delete()
        print

    def test_U1(self):
        """
        Tests that U1 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (GLOBAL, my area)
            S2 "@global"        : M1 (LOCAL), M2 (GLOBAL, my area), M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (GLOBAL, my area)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : No Match
            S7 "@private"       : M8 (PRIVATE to U5)

        """
        member = Member.objects.get(fullname="Freya Hum")
        print '[U1]', member.fullname, ', Area:', member.area
        se = SearchEngine(account=member, verbose=True)
        searches = [
            ("@local",          [1,2]),
            ("@global",         [1,2,5]),
            ("#se16",           [1,2]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        []),
            ("@private",        [8]),
        ]
        for terms, expected in searches:
            print "[U1] Test {} in {}".format(terms, expected)
            results = se.search(terms)
            print " >>", [self.getId(r) for r in results]
            self.assertQuerysetEqual(results, expected, self.getId, ordered=False)

    def test_U2(self):
        """
        Tests that U2 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (LOCAL)
            S2 "@global"        : M1 (LOCAL), M2 (LOCAL), M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (LOCAL)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : M3 (OWN, FRIEND), M4 (Friend), M5 (Friend), M6 (Friend)
            S7 "@private"       : M7 (PRIVATE from U5)

        """
        member = Member.objects.get(fullname="Suzanna Cole")
        print '[U2]', member.fullname, ', Area:', member.area
        se = SearchEngine(account=member, verbose=True)
        searches = [
            ("@local",          [1,2]),
            ("@global",         [1,2,5]),
            ("#se16",           [1,2]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        [3,4,5,6]),
            ("@private",        [7]),
        ]
        for terms, expected in searches:
            print "[U2] Test {} in {}".format(terms, expected)
            results = se.search(terms)
            print " >>", [self.getId(r) for r in results]
            self.assertQuerysetEqual(results, expected, self.getId, ordered=False)

    def test_U3(self):
        """
        Tests that U3 sees, for the followng searches:
            S1 "@local"         : M1 (LOCAL), M2 (GLOBAL, my area), M3 (FRIEND, my area)
            S2 "@global"        : M1 (LOCAL), M2 (GLOBAL, my area), M3 (FRIEND, my area), M5 (GLOBAL, outside area)
            S3 "#se16"          : M1 (LOCAL), M2 (GLOBAL, my area), M3 (FRIEND, my area)
            S4 "#se22"          : No Match
            S5 "#se22 @global"  : M5 (GLOBAL, outside area)
            S6 "@friends"       : M1 (Friend), M2 (Friend), M3 (Friend) 
            S7 "@private"       : No Match

        """
        member = Member.objects.get(fullname="Amanda Poke")
        print '[U3]', member.fullname, ', Area:', member.area
        se = SearchEngine(account=member, verbose=True)
        searches = [
            ("@local",          [1,2,3]),
            ("@global",         [1,2,3,5]),
            ("#se16",           [1,2,3]),
            ("#se22",           []),
            ("#se22 @global",   [5]),
            ("@friends",        [1,2,3]),
            ("@private",        []),
        ]
        for terms, expected in searches:
            print "[U3] Test {} in {}".format(terms, expected)
            results = se.search(terms)
            print " >>", [self.getId(r) for r in results]
            self.assertQuerysetEqual(results, expected, self.getId, ordered=False)

    def test_U4(self):
        """
        Tests that U4 sees, for the followng searches:
            S1 "@local"         : M4 (LOCAL), M5 (GLOBAL, my area)
            S2 "@global"        : M2 (GLOBAL, outside area), M4 (LOCAL), M5 (GLOBAL, my area)
            S3 "#se16"          : No Match
            S4 "#se22"          : M4 (LOCAL), M5 (GLOBAL, my area)
            S5 "#se22 @global"  : M4 (LOCAL), M5 (GLOBAL, my area)
            S6 "@friend"        : No Match
            S7 "@private"       : No Match 

        """
        member = Member.objects.get(fullname="Rachel Chatter")
        print '[U4]', member.fullname, ', Area:', member.area
        se = SearchEngine(account=member, verbose=True)
        searches = [
            ("@local",          [4,5]),
            ("@global",         [2,4,5]),
            ("#se16",           []),
            ("#se22",           [4,5]),
            ("#se22 @global",   [4,5]),
            ("@friends",        []),
            ("@private",        []),
        ]
        for terms, expected in searches:
            print "[U4] Test {} in {}".format(terms, expected)
            results = se.search(terms)
            print " >>", [self.getId(r) for r in results]
            self.assertQuerysetEqual(results, expected, self.getId, ordered=False)

    def test_U5(self):
        """
        Tests that U5 sees, for the followng searches:
            S1 "@local"         : M4 (LOCAL), M5 (LOCAL)
            S2 "@global"        : M2 (GLOBAL, outside area), M4 (LOCAL), M5 (LOCAL)
            S3 "#se16"          : No Match
            S4 "#se22"          : M4 (LOCAL), M5 (LOCAL)
            S5 "#se22 @global"  : M4 (LOCAL), M5 (LOCAL)
            S6 "@friend"        : M1 (Friend), M2 (Friend), M3 (Friend), M6 (OWN, FRIENDS)
            S7 "@private"       : M7 (PRIVATE to U2), M8 (PRIVATE from U1)

        """
        member = Member.objects.get(fullname="Sarah Parker")
        print '[U5]', member.fullname, ', Area:', member.area
        se = SearchEngine(account=member, verbose=True)
        searches = [
            ("@local",          [4,5]),
            ("@global",         [2,4,5]),
            ("#se16",           []),
            ("#se22",           [4,5]),
            ("#se22 @global",   [4,5]),
            ("@friends",        [1,2,3,6]),
            ("@private",        [7,8]),
        ]
        for terms, expected in searches:
            print "[U5] Test {} in {}".format(terms, expected)
            results = se.search(terms)
            print " >>", [self.getId(r) for r in results]
            self.assertQuerysetEqual(results, expected, self.getId, ordered=False)
