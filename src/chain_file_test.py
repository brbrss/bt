import unittest
import chain_file


def set_file(fp, s):
    f = open(fp, 'wb')
    f.write(s)
    f.close()


class ChainFileTest(unittest.TestCase):

    def test_read(self):
        a = './resource/multi/1.part'
        b = './resource/multi/2.part'
        s1 = bytes([i for i in range(33)])
        s2 = b'abcdefg'
        set_file(a, s1)
        set_file(b, s2)
        fl = [a, b]
        cf = chain_file.ChainFile(fl)
        res = cf.read(0, 35)
        self.assertEqual(res[33:], b'ab')
        self.assertEqual(cf.read(33, 2), b'ab')
        self.assertEqual(cf.read(32, 2), b'\x20a')


    def test_write(self):
        root = './resource/multi/m/'
        fl = []
        for i in range(6):
            fp = root+str(i)
            fl.append(fp)
            set_file(fp, b'12345')
        # 30 bytes in 6 files
        cf = chain_file.ChainFile(fl)
        s = bytes([i for i in range(5,30)])
        cf.write(5,s)
        cf.close()
        f = open(fl[5], 'rb')
        s5 = f.read()
        f.close()
        self.assertEqual(s5, bytes([i for i in range(25, 30)]))
