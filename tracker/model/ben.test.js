let encode = require('./ben');

it('encode', async () => {
    expect(encode(-1)).toBe('i-1e');
    expect(encode('free')).toBe('4:free');
});



it('encode array', async () => {
    expect(encode(['free', 67])).toBe('l4:freei67ee');
});

it('encode dict', async () => {
    expect(encode({ 'free': 67 })).toBe('d4:freei67ee');
});


