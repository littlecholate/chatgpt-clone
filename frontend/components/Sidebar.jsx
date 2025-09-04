'use client';
import React, { useState } from 'react';
import { Menu as MenuIcon, MessageSquarePlus, CircleUserRound, Search, LogOut, Paperclip } from 'lucide-react';
import ChatLabel from './ChatLabel';
import { useAppContext } from '@/context/AppContext';
import Link from 'next/link';
import toast from 'react-hot-toast';

const Sidebar = () => {
    const [expand, setExpand] = useState(true);
    const { user, chats, setSelectedChat, createNewChat, token, setToken } = useAppContext();
    const [search, setSearch] = useState('');

    const handleLogout = () => {
        localStorage.removeItem('token');
        setToken(null);
        toast.success('Logged out successfully');
    };

    return (
        <div className={`pt-8 pb-8 p-4 flex flex-col justify-between bg-[#212327] z-50 ${expand ? 'w-96' : 'w-20'}`}>
            <div>
                <div className={`${expand ? 'flex items-center justify-between' : 'flex-center'}`}>
                    {expand && (
                        <Link href="/" className="mx-auto text-xl text-white">
                            Chat Bot
                        </Link>
                    )}
                    <button
                        onClick={() => (expand ? setExpand(false) : setExpand(true))}
                        className="shrink-icon rounded-lg flex-center text-white cursor-pointer"
                    >
                        <MenuIcon size={24} />
                    </button>
                </div>

                <button
                    className={`mt-8 mx-auto w-full rounded-lg flex-center text-white cursor-pointer ${
                        expand ? 'gap-4 p-4 bg-gray-600 hover:opacity-90' : 'shrink-icon'
                    }`}
                    onClick={createNewChat}
                >
                    <MessageSquarePlus size={24} />
                    {expand && <p>Create New Chat</p>}
                </button>

                {/* Search Conversations */}
                <div
                    className={`gap-2 p-3 mt-4 flex items-center border border-white/20 text-white rounded-md ${
                        expand ? 'block' : 'hidden'
                    }`}
                >
                    <Search size={24} />
                    <input
                        onChange={(e) => setSearch(e.target.value)}
                        value={search}
                        type="text"
                        placeholder="Search history chat"
                        className="w-full text-sm placeholder:text-gray-100 outline-none"
                    />
                </div>

                <div className={`mt-8 text-white/25 text-sm ${expand ? 'block' : 'hidden'}`}>
                    <p className="my-1">Recents</p>
                    {/* chat label */}
                    <div>
                        {chats
                            .filter((chat) =>
                                chat.messages[0]
                                    ? chat.messages[0]?.content.toLowerCase().includes(search.toLowerCase())
                                    : chat.name.toLowerCase().includes(search.toLowerCase())
                            )
                            .map((chat) => (
                                <Link href="/" key={chat.id} onClick={() => setSelectedChat(chat)}>
                                    <ChatLabel chat={chat} />
                                </Link>
                            ))}
                    </div>
                </div>
            </div>

            <div>
                <Link href="/attachments">
                    <button
                        className={`mx-auto w-full rounded-lg flex-center text-white cursor-pointer ${
                            expand ? 'gap-4 p-4 bg-gray-600 hover:opacity-90' : 'shrink-icon'
                        }`}
                    >
                        <Paperclip size={24} />
                        {expand && <p>Attachments</p>}
                    </button>
                </Link>
                {/* user account */}
                <Link
                    href={user ? '/' : '/login'}
                    onClick={() => {
                        if (user) {
                            handleLogout();
                        }
                    }}
                    className={`mt-8 p-4 gap-12 mx-auto w-full rounded-lg flex-center text-white cursor-pointer ${
                        expand ? 'hover:bg-white/10' : 'shrink-icon'
                    }`}
                >
                    <CircleUserRound size={24} />
                    {expand && <p>{user ? user.username : 'Login your account'}</p>}
                    {user && <LogOut size={24} />}
                </Link>
            </div>
        </div>
    );
};

export default Sidebar;
