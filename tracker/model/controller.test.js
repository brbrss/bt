let controller = require('./controller');
const db = require('./peerdb');



it('ipv4', async () => {
    let peer = { ip: '13.5.10.255', port: 258 }
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u000d\u0005\u000a\u00ff\u0001\u0002');
});


it('ipv6 localhost', async () => {
    let peer = { ip: '::1', port: 258 }
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u007f\u0000\u0000\u0001\u0001\u0002');
});

it('ipv6 short', async () => {
    let peer = { ip: '::ffff:102:304', port: 258 }
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u0001\u0002\u0003\u0004\u0001\u0002');
});

it('ipv6 long', async () => {
    let peer = { ip: '0:0:0:0:0:ffff:0102:0304', port: 258 }
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u0001\u0002\u0003\u0004\u0001\u0002');
});

it('ipv6 bad', async () => {
    let peer = { ip: '10:20:20:0:0:ffff:0102:0304', port: 258 };
    expect(() => controller.encodePeer(peer)).toThrow();
});




it('announce start', async () => {
    const ip = '13.5.10.255';
    let query = {
        port: '258',
        event: 'started',
        uploaded: '0',
        downloaded: '0',
        left: '199300',
        info_hash: '12345678901234567890'
    };
    const res = controller.announce(query, ip);
    const target = 'd8:completei0e10:downloadedi0e10:incompletei0e8' +
        ':intervali180e12:min intervali60e5:peers0:6:peers60:10:tracker_id15:13.5.10.255>258e';
    expect(res).toBe(target);
});

it('announce two', async () => {
    db.reset();
    let ip = '65.66.67.68';
    let query = {
        port: '24930', // = 97*256+98
        event: 'started',
        uploaded: '0',
        downloaded: '123456',
        left: '0',
        info_hash: '12345678901234567890'
    };
    controller.announce(query, ip);
    ip = '13.95.90.255';
    query.downloaded = '0';
    query.left = '123456';
    const res = controller.announce(query, ip);

    const target = 'd8:completei0e10:downloadedi0e10:incompletei1e8:intervali180e12:min intervali60e5:peers6:' +
        'ABCDab6:peers60:10:tracker_id18:13.95.90.255>24930e';
    expect(res).toBe(target);

    query.event = undefined;
    controller.announce(query, ip);
    query.event = 'completed';
    controller.announce(query, ip);
    query.event = 'stopped';
    controller.announce(query, ip);

});