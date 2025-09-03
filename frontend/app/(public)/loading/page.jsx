'use client';
import { useRouter } from 'next/navigation';
import React, { useEffect } from 'react';

const Loading = () => {
    const router = useRouter();

    useEffect(() => {
        const timeout = setTimeout(() => {
            router.push('/');
        }, 8000);
        return () => clearTimeout(timeout);
    }, []);
    return (
        <div className="fixed top-0 left-0 flex-center h-screen w-screen text-white text-2xl z-[9999]">
            <div className="w-10 h-10 rounded-full border-4 border-white border-t-transparent animate-spin"></div>
        </div>
    );
};

export default Loading;
