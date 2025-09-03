export const dummyUserData = {
    _id: '123456789',
    name: 'cholate',
    email: 'cholate@gamil.com',
    password: '123',
};

const markdown = `
# Heading 1
## Heading 2
### Heading 3

This is **bold text** and *italic text*.

\`inline code\`

\`\`\`javascript
console.log("code block");
\`\`\`

- List item
# Heading 1
## Heading 2
### Heading 3

This is **bold text** and *italic text*.This is **bold text** and *italic text*.This is **bold text** and *italic text*.This is **bold text** and *italic text*.This is **bold text** and *italic text*.This is **bold text** and *italic text*.This is **bold text** and *italic text*.

\`inline code\`

\`\`\`javascript
    const [user, setUser] = useState(null);
    const [chats, setChats] = useState([]);
    const [selectedChat, setSelectedChat] = useState(null);

    const fetchUser = async () => {
        setUser(dummyUserData);
    };

    const fetchUsersChats = async () => {
        setChats(dummyChats);
        setSelectedChat(dummyChats[0]);
    };

    useEffect(() => {
        // If user login
        if (user) {
            fetchUsersChats();
        } else {
            setChats([]);
            setSelectedChat(null);
        }
    }, [user]);

    useEffect(() => {
        fetchUser();
    }, []);
\`\`\`

- List item
`;

export const dummyChats = [
    {
        _id: '123456456',
        userId: '121212',
        userName: 'cholate',
        name: 'New Chat',
        messages: [
            {
                role: 'user',
                content: 'In python orm example, what does the relationship means? Do I need it if I want the foreign key?',
                timestamp: '2025-09-03 20:12:00.123456',
            },
            {
                role: 'bot',
                content: markdown,
                timestamp: '2025-09-03 20:12:00.123456',
            },
            {
                role: 'user',
                content: 'In python orm example, what does the relationship means? Do I need it if I want the foreign key?',
                timestamp: '2025-09-03 20:12:00.123456',
            },
        ],
    },
    {
        _id: '123456457',
        userId: '121212',
        userName: 'cholate',
        name: 'New Chat',
        messages: [
            {
                role: 'user',
                content: 'In python orm example, what does the relationship means? Do I need it if I want the foreign key?',
                timestamp: '2025-09-03 20:12:00.123456',
            },
            { role: 'bot', content: 'nonono' },
        ],
        timestamp: '2025-09-03 20:12:00.123456',
    },
];
