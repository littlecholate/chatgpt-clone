import React from 'react';
import { SquarePen, Trash2 } from 'lucide-react';
import { useAppContext } from '@/context/AppContext';
import toast from 'react-hot-toast';

const ChatLabel = ({ chat }) => {
    const { axios, setChats, selectedChat, fetchUsersChats } = useAppContext();

    const handleDeleteChat = async (e, chatId) => {
        try {
            e.stopPropagation();
            const confirm = window.confirm('Are you sure ?');
            if (!confirm) return;
            const { data } = await axios.delete(`/chat/${chatId}`);

            if (data) {
                setChats((prev) => prev.filter((chat) => chat.id !== chatId));
                await fetchUsersChats();
                toast.success(data.message);
            }
        } catch (error) {
            toast.error(error.message);
        }
    };

    return (
        <>
            <div
                className={`mt-2 p-2 flex items-center justify-between rounded-lg text-white/80 hover:bg-white/10 group cursor-pointer ${
                    chat.id === selectedChat.id ? 'bg-white/10' : ''
                }`}
            >
                <p className="py-2 truncate">{chat.messages.length > 0 ? chat.messages[0].content.slice(0, 32) : chat.name}</p>
                {/* rename and delete icon */}
                <div className="ml-4 flex-center group">
                    <div className="px-3 py-2 hover:bg-white/10 rounded-lg hidden group-hover:block">
                        <SquarePen size={20} />
                    </div>
                    <div
                        className="px-3 py-2 hover:bg-white/10 rounded-lg hidden group-hover:block"
                        onClick={(e) => toast.promise(handleDeleteChat(e, chat.id), { loading: 'deleting...' })}
                    >
                        <Trash2 size={20} />
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatLabel;
