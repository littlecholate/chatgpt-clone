'use client';
import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAppContext } from './AppContext';

export default function ProtectedRoute() {
    const router = useRouter();
    const pathname = usePathname();
    const { user, setUser } = useAppContext();

    useEffect(() => {
        fetch('http://127.0.0.1:8000/docs#/protected')
            .then((res) => res.json())
            .then((data) => {
                if (!data.user && pathname !== '/login') {
                    router.push('/login');
                } else {
                    setUser(data.user);
                }
            });
    }, [pathname]);

    if (!user) return null; // hide content while redirecting
    return <>{children}</>;
}
