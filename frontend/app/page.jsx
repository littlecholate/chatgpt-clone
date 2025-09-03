'use client';
import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import PromptBox from '@/components/PromptBox';
import Message from '@/components/Message';

export default function Home() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    return (
        <>
            <div className="relative px-4 pb-8 flex-1 flex-center flex-col text-white bg-[#292a2d]">
                {messages.length === 0 ? (
                    <>
                        <p className="text-2xl">Hi, how can I help you?</p>
                    </>
                ) : (
                    <div>
                        <Message role="user" content="What is next js?" />
                    </div>
                )}
                {/* prompt box */}
                <PromptBox isLoading={isLoading} setIsLoading={setIsLoading} />
                <p className="absolute bottom-1 text-xs text-gray-500">2025</p>
            </div>
        </>
    );
}
