let ben = require('./ben');

it('ben.encode', async () => {
    expect(ben.encode(-1)).toBe('i-1e');
    expect(ben.encode('free')).toBe('4:free');
});



it('ben.encode array', async () => {
    expect(ben.encode(['free', 67])).toBe('l4:freei67ee');
});

it('ben.encode dict', async () => {
    expect(ben.encode({ 'free': 67 })).toBe('d4:freei67ee');
});

it('ben.encode dict order', async () => {
    expect(ben.encode({ 'free': 67 ,'a':9})).toBe('d1:ai9e4:freei67ee');
});


