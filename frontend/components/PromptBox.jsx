import React from 'react';
import { useState } from 'react';
import { Paperclip, Airplay, Brain } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAppContext } from '@/context/AppContext';

const PromptBox = ({ isLoading, setIsLoading, selectedChat, setMessages }) => {
    const [prompt, setPrompt] = useState('');
    const [mode, setMode] = useState([]);
    const { user, axios, token, setToken } = useAppContext();

    const handleSubmit = async (e) => {
        try {
            e.preventDefault();
            if (isLoading) return;
            if (!user) return toast('Login to send messages');
            setIsLoading(true);

            const promptCopy = prompt;
            setPrompt('');
            // set user prompt messages
            setMessages((prev) => [...prev, { role: 'user', content: prompt, create_date: Date.now() }]);

            const { data } = await axios.post(`/chat/${selectedChat.id}/messages`, { role: 'user', content: prompt });

            if (data) {
                // set robot messages
                setMessages((prev) => [...prev, { role: 'robot', content: data.content, create_date: data.create_date }]);
            } else {
                setPrompt(promptCopy);
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setPrompt('');
            setIsLoading(false);
        }
    };

    return (
        <form
            className={`mt-8 p-6 w-full ${false ? 'max-w-3xl' : 'max-w-5xl'} rounded-3xl bg-[#404045] transition-all`}
            onSubmit={handleSubmit}
        >
            <input
                className="outline-none w-full text-xl resize-none overflow-hidden break-words bg-transparent"
                rows={1}
                placeholder="Enter your questions."
                required
                onChange={(e) => setPrompt(e.target.value)}
                value={prompt}
            />

            <div className="mt-8 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <p className="px-4 py-2 gap-2 text-sm flex items-center border border-gray-300/40 rounded-full cursor-pointer hover:bg-gray-500/20 transition">
                        <Brain size={24} />
                        Think
                    </p>
                    <p className="px-4 py-2 gap-2 text-sm flex items-center border border-gray-300/40 rounded-full cursor-pointer hover:bg-gray-500/20 transition">
                        <Airplay size={24} />
                        Search
                    </p>
                    <p className="px-4 py-2 gap-2 text-sm flex items-center border border-gray-300/40 rounded-full cursor-pointer hover:bg-gray-500/20 transition">
                        <Paperclip size={24} />
                        RAG
                    </p>
                </div>
            </div>
        </form>
    );
};

export default PromptBox;
