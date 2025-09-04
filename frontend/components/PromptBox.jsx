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
        e.preventDefault();
        if (isLoading) return;
        if (!user) return toast('Login to send messages');

        try {
            setIsLoading(true);

            const promptCopy = prompt;
            setPrompt('');
            // 1. set user prompt messages immediately
            setMessages((prev) => [...prev, { role: 'user', content: prompt, create_date: Date.now() }]);

            // 2. create a placeholder robot message we'll keep appending to
            const robotId = crypto?.randomUUID?.() || String(Date.now());
            setMessages((prev) => [...prev, { id: robotId, role: 'robot', content: '', create_date: Date.now() }]);

            // 3. stream messages from backend
            // cannot use axios, Fetch (with res.body.getReader()) is the only browser-native way today to consume a streaming body. - by chatgpt
            const res = await fetch(`http://127.0.0.1:8000/chat/${selectedChat.id}/messages/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // If you use JWT:
                    // ...(user?.token ? { Authorization: `Bearer ${user.token}` } : {}),
                },
                body: JSON.stringify({ content: promptCopy }),
            });
            if (!res.ok || !res.body) {
                throw new Error(`HTTP ${res.status}`);
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            // 4. read SSE chunks
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // SSE messages are separated by a blank line
                const parts = buffer.split('\n\n');
                buffer = parts.pop() || '';

                for (const chunk of parts) {
                    // we only care about "data:" lines and "event:done"
                    const lines = chunk.split('\n');
                    let event = 'message';
                    let data = '';

                    for (const line of lines) {
                        if (!line) continue;
                        if (line.startsWith(':')) continue; // comment/heartbeat
                        if (line.startsWith('event:')) event = line.slice(6).trim();
                        else if (line.startsWith('data:')) data += line.slice(5);
                    }

                    if (event === 'done') {
                        // finished
                        continue;
                    }

                    if (data) {
                        // append token(s) to the robot message
                        setMessages((prev) =>
                            prev.map((m) => (m.id === robotId ? { ...m, content: (m.content || '') + data } : m))
                        );
                    }
                }
            }

            // flush any remainder (rare)
            if (buffer.startsWith('data:')) {
                const leftover = buffer.slice(5);
                setMessages((prev) => prev.map((m) => (m.id === robotId ? { ...m, content: (m.content || '') + leftover } : m)));
            }

            // original code
            // const { data } = await axios.post(`/chat/${selectedChat.id}/messages`, { role: 'user', content: prompt });

            // if (data) {
            //     // set robot messages
            //     setMessages((prev) => [...prev, { role: 'robot', content: data.content, create_date: data.create_date }]);
            // } else {
            //     setPrompt(promptCopy);
            // }
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
