"""For decoding bencode"""


class ParseError(RuntimeError):
    pass


# types:
# '' str
# i int
# l list
# d dict




def _parse_int(s,a,b):
    k = a + 1
    while k<b and s[k]!='e':
        k+=1
    if k==b:
        raise ParseError('No ending "e" for int')
    res = int(s[a+1:k])
    if res==0 and s[a+1] == '-':
        raise ParseError('-0 for int not allowed')
    if res>0 and s[a+1] == '0':
        raise ParseError('Leading 0 for int not allowed')
    if res<0 and s[a+2] == '0':
        raise ParseError('Leading 0 for int not allowed')
    return res, (k+1)

def _parse_str(s,a,b):
    k = a + 1
    while k<b and s[k]!=':':
        k+=1
    size = int(s[a:k])
    end = k+1+size
    res = str(s[k+1:end])
    return res,end


def _parse_list(s,a,b):
    #s[a]=='l'
    k = a + 1
    res = []
    while s[k]!='e':
        item,k = _parse(s,k,b)
        res.append(item)
    if k>= b:
        raise ParseError('No ending "e" for list')
    return res,k+1

def _parse_dict(s,a,b):
    #s[a]=='d'
    k = a + 1
    res = []
    while s[k]!='e':
        item,k = _parse(s,k,b)
        res.append(item)
    if k>= b:
        raise ParseError('No ending "e" for dict')
    if len(res) % 2 != 0:
        raise ParseError('Number of items in dict is not even')
    d = {}
    for i in range(len(res)//2):
        key = res[i*2]
        if i*2+2<len(res) and res[i*2+2]<key:
            raise ParseError('Key in dict not sorted')
        val = res[i*2+1]
        d[key] = val
    return d,k+1    

def _parse(s,a,b):
    '''parse substring of s for a<= i < b'''
    if s[a] == 'i':
        return _parse_int(s,a,b)
    elif s[a] == 'l':
        return _parse_list(s,a,b)
    elif s[a] == 'd':
        return _parse_dict(s,a,b)
    elif s[a].isnumeric():
        return _parse_str(s,a,b)

def parse(s):
    res,k = _parse(s,0,len(s))
    if k != len(s):
        raise ParseError('Not all content is consumed')
    return res

def parse_file(fp):
    f = open(fp,'rb')
    s = f.read()
    f.close()
    s = str(s,'latin1')
    d = parse(s)
    return d

def encode(d):
    f = lambda item:encode(item)
    if type(d) is str:
        return str(len(d))+':'+d
    elif type(d) is int:
        return 'i'+str(d)+'e'
    elif type(d) is list:
        return 'l' + ''.join([f(t) for t in d]) + 'e'
    elif type(d) is dict:
        ls = list(d.keys())
        ls.sort()
        return 'd' + ''.join([f(t)+f(d[t]) for t in ls]) + 'e'
    raise RuntimeError('Unsupported type'+type(d))
