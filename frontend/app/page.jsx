'use client';
import { useState, useEffect, useRef } from 'react';
import PromptBox from '@/components/PromptBox';
import Message from '@/components/Message';
import { useAppContext } from '@/context/AppContext';

export default function Home() {
    const containerRef = useRef(null);

    const { selectedChat, axios } = useAppContext();
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const fetchSelectedChatMessages = async () => {
        try {
            setIsLoading(true);
            const { data } = await axios.get(`/chat/${selectedChat.id}/messages`);

            if (data) {
                setMessages(data);
            }
        } catch (error) {
            toast.error(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // When selectedChat is changed, rerender the component
    useEffect(() => {
        if (selectedChat) {
            // console.log('selected chat data: ' + JSON.stringify(selectedChat));
            fetchSelectedChatMessages();
        }
    }, [selectedChat]);

    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTo({
                top: containerRef.current.scrollHeight,
                behavior: 'smooth',
            });
        }
    }, [messages]);

    return (
        <>
            {/* chat box */}
            {messages.length === 0 ? (
                <>
                    <p className="text-2xl">Hi, how can I help you?</p>
                </>
            ) : (
                <div ref={containerRef} className="w-full max-w-5xl h-[600px] overflow-auto">
                    {messages.map((message, index) => (
                        <Message key={index} message={message} />
                    ))}
                </div>
            )}

            {/* loading animation */}
            {isLoading && (
                <div className="loader mt-6 flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-50 animate-bounce"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-50 animate-bounce"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-50 animate-bounce"></div>
                </div>
            )}
            {/* prompt box */}
            <PromptBox isLoading={isLoading} setIsLoading={setIsLoading} setMessages={setMessages} selectedChat={selectedChat} />
        </>
    );
}
