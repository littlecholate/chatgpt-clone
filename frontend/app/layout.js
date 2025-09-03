import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import '../assets/prism.css';
import { AppContextProvider } from '@/context/AppContext';
import Sidebar from '@/components/Sidebar';

const geistSans = Geist({
    variable: '--font-geist-sans',
    subsets: ['latin'],
});

const geistMono = Geist_Mono({
    variable: '--font-geist-mono',
    subsets: ['latin'],
});

export const metadata = {
    title: 'ChatGPT Clone',
    description: 'ChatGPT-like project',
};

export default function RootLayout({ children }) {
    return (
        <AppContextProvider>
            <html lang="en">
                <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
                    <div className="h-screen flex">
                        {/* -- sidebar -- */}
                        <Sidebar />
                        <div className="relative px-4 pb-8 flex-1 flex-center flex-col text-white bg-[#292a2d]">{children}</div>
                    </div>
                </body>
            </html>
        </AppContextProvider>
    );
}
