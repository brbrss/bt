import unittest
import ben

class BenTest(unittest.TestCase):

    def test_str(self):
        s = '4:spam'
        self.assertEqual(ben.parse(s), 'spam')

    def test_int(self):
        s = 'i3e'
        self.assertEqual(ben.parse(s), 3)
        self.assertEqual(ben.parse('i40e'), 40)

    def test_int_03(self):
        s = 'i03e'
        with self.assertRaises(ben.ParseError):
            ben.parse(s)
    
    def test_int_minus03(self):
        s = 'i-030e'
        with self.assertRaises(ben.ParseError):
            ben.parse(s)
    
    def test_int_minus0(self):
        s = 'i-0e'
        with self.assertRaises(ben.ParseError):
            ben.parse(s)
    

    def test_list(self):
        s = 'l4:spam4:eggse'
        self.assertEqual(ben.parse(s), ['spam','eggs'])

    def test_dict_simple(self):
        s = 'd3:cow3:moo4:spam4:eggse'
        self.assertEqual(ben.parse(s), {'cow': 'moo', 'spam': 'eggs'})
    
    def test_dict_tested(self):
        s = 'd4:spaml1:a1:bee'
        self.assertEqual(ben.parse(s), {'spam': ['a', 'b']})
    
    def test_dict_order(self):
        s = 'd4:spam4:eggs3:cow3:mooe'
        with self.assertRaises(ben.ParseError):
            ben.parse(s)
    
    def test_encode(self):
        self.assertEqual(ben.encode('spam'),'4:spam')
        self.assertEqual(ben.encode(-64),'i-64e')
        ls = [6,[5,3]]
        self.assertEqual(ben.encode(ls),'li6eli5ei3eee')


    def test_encode_dist(self):
        d = {10-t:t for t in range(2)}
        s = ben.encode(d)
        self.assertEqual(s,'di9ei1ei10ei0ee')
    

if __name__ == '__main__':
    unittest.main()