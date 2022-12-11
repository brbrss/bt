
const ben = {};

ben.encode = function (data) {
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
            res += ben.encode(item);
        }
        res += 'e';
        return res;
    } else if (typeof data === 'object') {
        let res = 'd';
        const keys = Object.keys(data).sort();
        for (k of keys) {
            res += ben.encode(k) + ben.encode(data[k]);
        }
        res += 'e';
        return res;
    } else {
        throw Error('Unsupported data: ' + data);
    }

}

module.exports = ben;
