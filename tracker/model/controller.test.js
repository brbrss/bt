let controller = require('./controller');



it('ipv4', async () => {
    let peer = {ip:'13.5.10.255',port:258}
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u000d\u0005\u000a\u00ff\u0001\u0002');
});


it('ipv6 localhost', async () => {
    let peer = {ip:'::1',port:258}
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u007f\u0000\u0000\u0001\u0001\u0002');
});

it('ipv6 short', async () => {
    let peer = {ip:'::ffff:102:304',port:258}
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u0001\u0002\u0003\u0004\u0001\u0002');
});

it('ipv6 long', async () => {
    let peer = {ip:'0:0:0:0:0:ffff:0102:0304',port:258}
    const res = controller.encodePeer(peer);
    expect(res).toBe('\u0001\u0002\u0003\u0004\u0001\u0002');
});

it('ipv6 bad', async () => {
    let peer = {ip:'10:20:20:0:0:ffff:0102:0304',port:258}
    expect(()=>controller.encodePeer(peer)).toThrow();
});