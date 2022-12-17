import unittest
from tracker import *


class TrackerTest(unittest.TestCase):

    def test_parse(self):
        s = '\x87\x00\x92¹\x1aá'
        res = parse_peer(s)
        self.assertEqual(res,  [((135, 0, 146, 185), 6881)])

    def test_err(self):
        d = {'failure reason': 'no peer_id supplied'}
        t = Tracker(d)
        self.assertEqual(t.err,  'no peer_id supplied')

    def test_good(self):
        d = {'complete': 0, 'downloaded': 0, 'incomplete': 1,
             'interval': 1867, 'min interval': 933, 'peers': '\x87\x00\x92¹\x1aá'}
        t = Tracker(d)
        self.assertEqual(t.err,  None)

    def test_missing(self):
        d = {'complete': 0, 'downloaded': 0, 'incomplete': 1,
             'interval': 1867, 'min interval': 933}
        t = Tracker(d)
        self.assertNotEqual(t.err,  None)
