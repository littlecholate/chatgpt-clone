export const dummyUserData = {
    _id: '123456789',
    name: 'cholate',
    email: 'cholate@gamil.com',
    password: '123',
};

export const dummyChats = [
    {
        _id: '123456456',
        userId: '121212',
        userName: 'cholate',
        name: 'New Chat',
        messages: [
            { role: 'user', content: 'hello' },
            { role: 'bot', content: 'hello' },
        ],
    },
    {
        _id: '123456457',
        userId: '121212',
        userName: 'cholate',
        name: 'New Chat',
        messages: [{ role: 'bot', content: 'nonono' }],
    },
];
