'use client';
import { useState } from 'react';
import Sidebar from '@/components/Sidebar';

export default function Home() {
    const [expand, setExpand] = useState(false);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    return (
        <div>
            <div className="h-screen flex">
                {/* -- sidebar -- */}
                <Sidebar expand={expand} setExpand={setExpand} />
                <div className="relative px-4 pb-8 flex-1 flex flex-col items-center justify-center text-white bg-[#292a2d]">
                    {messages.length === 0 ? (
                        <>
                            <p className="text-2xl">Hi, how can I help you?</p>
                        </>
                    ) : (
                        <div></div>
                    )}
                    {/* prompt box */}
                    <p className="absolute bottom-1 text-xs text-gray-500">2025</p>
                </div>
            </div>
        </div>
    );
}
