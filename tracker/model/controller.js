const db = require('./peerdb');
const ipaddr = require('ipaddr.js');

const controller = {};


function arreq(a,b){
    if(a.length!=b.length){
        return false;
    }
    for(let i =0;i<a.length;i++){
        if(a[i]!==b[i]){
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
            if(arreq(rep.parts,[0,0,0,0,0,0,0,1])){
                iparr = [127,0,0,1];
            }else if(rep.isIPv4MappedAddress()){
                iparr = rep.toIPv4Address().octets;
            }else{
                console.log(rep);
                throw Error('Ipv6 not supported')
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
    d['peers'] = '';
    d['peers6'] = ''
}

function onStart(query, ip) {
    const port = query.port;
    const info_hash = query.info_hash;
    const completed = query.left === '0';
    const peerList = db.get(info_hash);
    const tracker_id = db.add(info_hash, ip, port, completed);
}

function onStop(query, ip) {
    db.remove(info_hash, ip, port);

}

function onCompolete(query, ip) {
    const tracker_id = query.tracker_id;
    if (tracker_id) {
        db.complete(info_hash, tracker_id);
    }
}

function onQuery(query, ip) {

}

function announce(query, ip) {
    const event = query.event;
    query.port = Number(query.port);
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
}


module.exports = controller;
