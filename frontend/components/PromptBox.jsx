import React from 'react';
import { useState } from 'react';
import { Paperclip, ArrowUp, Airplay, Brain } from 'lucide-react';

const PromptBox = ({ isLoading, setIsLoading }) => {
    const [prompt, setPrompt] = useState('');

    return (
        <form className={`mt-16 p-6 w-full ${false ? 'max-w-3xl' : 'max-w-5xl'} rounded-3xl bg-[#404045] transition-all`}>
            <textarea
                className="outline-none w-full text-xl resize-none overflow-hidden break-words bg-transparent"
                rows={2}
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

                <button className={`p-2 rounded-full ${prompt.trim() ? 'bg-primary' : 'bg-[#71717a]'} cursor-pointer`}>
                    <ArrowUp size={24} />
                </button>
            </div>
        </form>
    );
};

export default PromptBox;
