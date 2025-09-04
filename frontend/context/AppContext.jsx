'use client';
import { dummyChats, dummyUserData } from '@/assets/dummyData';
import { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

axios.defaults.baseURL = 'http://127.0.0.1:8000/';

const AppContext = createContext();

export const AppContextProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [chats, setChats] = useState([]);
    const [selectedChat, setSelectedChat] = useState(null);
    const [token, setToken] = useState(null);
    const [isLoadingUser, setIsLoadingUser] = useState(true);

    const fetchUser = async () => {
        try {
            const { data } = await axios.get('/protected', { headers: { Authorization: `Bearer ${token}` } });
            if (data.success) {
                console.log(data);
                setUser(data.user);
            } else {
                toast.error(data.message);
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setIsLoadingUser(false);
        }
    };

    const fetchUsersChats = async () => {
        try {
            const { data } = await axios.get('/chat', { headers: { Authorization: `Bearer ${token}` } });
            if (data.success) {
                setChats(data.chats);
                if (data.chats.length === 0) {
                    await createNewChat();
                    return fetchUsersChats();
                } else {
                    setSelectedChat(data.chats[0]);
                }
            } else {
                toast.error(data.message);
            }
        } catch (error) {
            toast.error(error.message);
        }
    };

    const createNewChat = async () => {
        try {
            if (!user) return toast('Login to create a new chat');
            // navigate to '/'
            await axios.get('/chat', { headers: { Authorization: `Bearer ${token}` } });
            await fetchUsersChats();
        } catch (error) {
            toast.error(error.message);
        }
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
        if (token) {
            fetchUser();
        } else {
            setUser(null);
            setIsLoadingUser(false);
        }
    }, [token]);

    useEffect(() => {
        const storedToken = localStorage.getItem('access_token');
        console.log('token: ' + storedToken);
        if (storedToken) {
            setToken(storedToken);
        }
    }, []);

    const value = {
        user,
        setUser,
        fetchUser,
        chats,
        setChats,
        selectedChat,
        setSelectedChat,
        createNewChat,
        token,
        setToken,
        isLoadingUser,
        fetchUsersChats,
        axios,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => useContext(AppContext);
