const db = require('./peerdb');
const ipaddr = require('ipaddr.js');
const ben = require('./ben');


const controller = {};


function arreq(a, b) {
    if (a.length != b.length) {
        return false;
    }
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) {
            return false;
        }
    }
    return true;
}

controller.encodePeer = function (peer) {
    let iparr;
    {
        const rep = ipaddr.parse(peer.ip);
        if (rep.parts) { //ipv6
            if (arreq(rep.parts, [0, 0, 0, 0, 0, 0, 0, 1])) {
                iparr = [127, 0, 0, 1];
            } else if (rep.isIPv4MappedAddress()) {
                iparr = rep.toIPv4Address().octets;
            } else {
                throw Error('Ipv6 not supported' + rep)
            }
        } else if (rep.octets) {//ipv4
            iparr = rep.octets;
        }
    }
    let res = '';
    for (let c of iparr) {
        cc = String.fromCharCode(c);
        res += cc;
    }
    const b = peer.port % 256;
    const a = (peer.port - b) / 256;
    res += String.fromCharCode(a);
    res += String.fromCharCode(b);
    return res;
}

controller.response = function (peerList) {
    const complete = peerList.filter(t => t.completed).length;
    const d = {};
    d['downloaded'] = complete;
    d['complete'] = complete;
    d['incomplete'] = peerList.length - complete;
    d['interval'] = 180;
    d['min interval'] = 60;
    let s = '';
    for (const p of peerList) {
        s += this.encodePeer(p);
    }
    d['peers'] = s;
    d['peers6'] = ''
    return d;
}

function onStart(query, ip) {
    const port = query.port;
    const info_hash = query.info_hash;
    const completed = query.left === '0';
    const peerList = db.get(info_hash, ip, port);
    const tracker_id = db.add(info_hash, ip, port, completed);
    const res = controller.response(peerList);
    res['tracker_id'] = tracker_id;
    return ben.encode(res);
}

function onStop(query, ip) {
    const port = query.port;
    db.remove(info_hash, ip, port);
    const res = controller.response([]);
    return ben.encode(res);
}

function onCompolete(query, ip) {
    const port = query.port;
    const tracker_id = query.tracker_id;
    if (tracker_id) {
        db.complete(info_hash, tracker_id);
    }
    const peerList = db.get(info_hash, ip, port);
    const res = controller.response(peerList);
    return ben.encode(res);
}

function onQuery(query, ip) {
    const port = query.port;
    const tracker_id = query.tracker_id;
    const completed = query.left === '0';
    const peerList = db.get(query.info_hash, ip, port);
    const new_id = db.add(query.info_hash, ip, query.port, completed);

    const res = controller.response(peerList);
    if (tracker_id !== new_id) {
        res['tracker_id'] = new_id;
    }
    return ben.encode(res);
}

controller.announce = function (query, ip) {
    if (Object.keys(query).length < 1) {
        const res = {};
        res['failure reason'] = 'no query parameters';
        return ben.encode(res);
    }
    try {
        const event = query.event;
        query.port = Number(query.port);
        query.uploaded = Number(query.uploaded);
        query.downloaded = Number(query.downloaded);
        query.info_hash = query.info_hash.toUpperCase()

        if (query.port % 1 !== 0) {
            throw Error('bad port num: ' + query.port);
        }
        if (event === 'started') {
            return onStart(query, ip);
        } else if (event === 'stopped') {
            return onStop(query, ip);
        } else if (event === 'completed') {
            return onCompolete(query, ip);
        } else { // not set
            return onQuery(query, ip);
        }
    } catch (err) {
        const res = {};
        res['failure reason'] = err.message;
        return ben.encode(res);
    }
}


module.exports = controller;
