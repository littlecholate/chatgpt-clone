import React, { useEffect } from 'react';
import { Copy, Pencil, RotateCcw, Bot } from 'lucide-react';
import moment from 'moment';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Prism from 'prismjs';

const Message = ({ message }) => {
    useEffect(() => {
        Prism.highlightAll();
    }, [message.content]);

    return (
        <div className="w-full flex flex-col items-center text-lg text-white/90">
            <div className={`w-full mb-8 flex flex-col ${message.role === 'user' && 'items-end'}`}>
                <div
                    className={`group relative flex py-3 rounded-xl ${
                        message.role === 'user' ? 'max-w-2xl bg-[#414158] px-5' : 'gap-3'
                    }`}
                >
                    {/* buttons under message */}
                    <div
                        className={`opacity-0 group-hover:opacity-100 absolute ${
                            message.role === 'user' ? '-left-16 top-2.5' : 'left-9 -bottom-6'
                        } transition-all`}
                    >
                        <div className="flex items-center gap-3 opacity-70">
                            {message.role === 'bot' && (
                                <>
                                    <Copy size={24} className="cursor-pointer" />
                                    <RotateCcw size={24} className="cursor-pointer" />
                                </>
                            )}
                        </div>
                    </div>
                    {/* main content */}
                    {message.role === 'user' ? (
                        <div className="flex flex-col gap-3">
                            <span>{message.content}</span>
                            <span className="text-sm opacity-70">{moment(message.create_date).fromNow()}</span>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-3">
                            <Bot size={36} />
                            <span className="reset-tw">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                            </span>
                            <span className="text-sm opacity-70">{moment(message.create_date).fromNow()}</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Message;
