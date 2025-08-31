import React from 'react';
import { Menu as MenuIcon, MessageSquarePlus, CircleUserRound } from 'lucide-react';

const Sidebar = ({ expand, setExpand }) => {
    return (
        <div className={`pt-8 pb-8 p-4 flex flex-col justify-between bg-[#212327] z-50 ${expand ? 'w-64' : 'w-20'}`}>
            <div>
                <div className={`${expand ? 'flex items-center justify-between' : 'flex-center'}`}>
                    {expand && <p className="mx-auto text-xl text-white">Chat Bot</p>}
                    <button
                        onClick={() => (expand ? setExpand(false) : setExpand(true))}
                        className="shrink-icon rounded-lg flex-center text-white cursor-pointer"
                    >
                        <MenuIcon size={24} />
                    </button>
                </div>

                <button
                    className={`mt-8 mx-auto w-full rounded-lg flex-center text-white cursor-pointer ${
                        expand ? 'gap-4 p-4 bg-gray-600 hover:opacity-90' : 'shrink-icon'
                    }`}
                >
                    <MessageSquarePlus size={24} />
                    {expand && <p>Create New Chat</p>}
                </button>

                <div className={`mt-8 text-white/25 text-sm ${expand ? 'block' : 'hidden'}`}>
                    <p className="my-1">Recents</p>
                    {/* chat label */}
                </div>
            </div>

            {/* user account */}
            <div
                className={`mx-auto w-full rounded-lg flex-center text-white cursor-pointer ${
                    expand ? 'gap-4 p-4 hover:bg-white/10' : 'shrink-icon'
                }`}
            >
                <CircleUserRound size={24} />
                {expand && <p>My Profile</p>}
            </div>
        </div>
    );
};

export default Sidebar;
