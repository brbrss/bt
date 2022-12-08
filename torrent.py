import ben
import hashlib
import urllib.request
import urllib.parse
import urllib.error


class Torrent(object):
    def __init__(self,fp):
        data = ben.parse_file(fp)
        self.announce = data['announce']
        self.info = data['info']
        infostr = bytes(ben.encode(self.info),'latin1')
        sha1 = hashlib.sha1()
        sha1.update(infostr)
        self.info_hash = sha1.digest() # bytes
        if 'length' in self.info:
            self.length = self.info['length']
        elif 'files' in self.info:
            self.length = sum([fl['length'] for fl in self.info['files']])

    def req_data(self):
        data = {
            'info_hash': self.info_hash,
            'peer_id':'ab123456781234567890',
            'port':6881,
            'uploaded':'0',
            'downloaded':'0',
            'left':str(self.length)
        }
        return data
    
    def tracker_get(self,url):
        data = urllib.parse.urlencode(self.req_data())
        req = urllib.request.Request(url+'?'+data,method='GET')
        res = None
        try:
            res = urllib.request.urlopen(req)
            s = res.read()
            s = str(s,'latin1')
            return ben.parse(s)
        except urllib.error.HTTPError as err:
            return err.read()
