import React from 'react';
import { SquarePen, Trash2 } from 'lucide-react';

const ChatLabel = () => {
    return (
        <>
            <div className="p-2 flex items-center justify-between rounded-lg text-white/80 hover:bg-white/10 group cursor-pointer">
                <p className="py-2 truncate">Chat name hereeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee</p>
                {/* rename and delete icon */}
                <div className="ml-4 flex-center group">
                    <div className="px-3 py-2 hover:bg-white/10 rounded-lg hidden group-hover:block">
                        <SquarePen size={20} />
                    </div>
                    <div className="px-3 py-2 hover:bg-white/10 rounded-lg hidden group-hover:block">
                        <Trash2 size={20} />
                    </div>
                </div>
            </div>
        </>
    );
};

export default ChatLabel;
