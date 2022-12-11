
function encode(data) {
    if (typeof data === 'string') {
        const sz = data.length;
        return String(sz) + ':' + data;
    } else if (typeof data === 'number') {
        if (data % 1 !== 0) {
            throw Error(data + ' is not int');
        }
        return 'i' + String(data) + 'e';
    }
    else if (Array.isArray(data)) {
        let res = 'l';
        for (item of data) {
            res += encode(item);
        }
        res += 'e';
        return res;
    } else if (typeof data === 'object') {
        let res = 'd';
        for (k in data) {
            res += encode(k) + encode(data[k]);
        }
        res += 'e';
        return res;
    } else {
        throw Error('Unsupported data: ' + data);
    }

}

module.exports = encode;
