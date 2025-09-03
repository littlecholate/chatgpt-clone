'use client';
import { dummyChats, dummyUserData } from '@/assets/dummyData';
import { createContext, useContext, useEffect, useState } from 'react';

const AppContext = createContext();

export const AppContextProvider = ({ children }) => {
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

    const value = { user, setUser, fetchUser, chats, setChats, selectedChat, setSelectedChat };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => useContext(AppContext);
