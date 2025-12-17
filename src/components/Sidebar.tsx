import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { MessageSquarePlus, Trash2, LogOut, User, Sun, Moon } from 'lucide-react';
import type { ChatSession } from '../types';

interface SidebarProps {
    sessions: ChatSession[];
    activeSession: ChatSession | null;
    onSelectSession: (session: ChatSession) => void;
    onNewChat: () => void;
    onDeleteSession: (sessionId: string) => void;
    isOpen: boolean;
    onToggle: () => void;
}

export default function Sidebar({
    sessions,
    activeSession,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    isOpen
}: SidebarProps) {
    const { user, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();

    if (!isOpen) return null;

    return (
        <div className="w-64 bg-white dark:bg-slate-950 flex flex-col border-r border-slate-200 dark:border-slate-800">
            {/* New Chat Button */}
            <div className="p-3 border-b border-slate-200 dark:border-slate-800">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                >
                    <MessageSquarePlus className="w-5 h-5" />
                    <span className="font-medium">New Chat</span>
                </button>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
                {sessions.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 dark:text-slate-500 text-sm">
                        No chat history yet
                    </div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            className={`group relative flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${activeSession?.id === session.id
                                    ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white'
                                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:text-slate-900 dark:hover:text-white'
                                }`}
                            onClick={() => onSelectSession(session)}
                        >
                            <MessageSquarePlus className="w-4 h-4 flex-shrink-0" />
                            <span className="flex-1 truncate text-sm">{session.title}</span>

                            {/* Delete button - shows on hover */}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    if (confirm('Delete this chat?')) {
                                        onDeleteSession(session.id);
                                    }
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-300 dark:hover:bg-slate-700 rounded transition-opacity"
                                title="Delete chat"
                            >
                                <Trash2 className="w-4 h-4 text-red-500 dark:text-red-400" />
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* User Profile, Theme Toggle & Logout */}
            <div className="p-3 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2 px-3 py-2 text-slate-700 dark:text-slate-300">
                    <div className="w-8 h-8 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center">
                        <User className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">{user?.name}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-500 truncate">{user?.email}</p>
                    </div>
                    <button
                        onClick={toggleTheme}
                        className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                    >
                        {theme === 'dark' ? (
                            <Sun className="w-4 h-4" />
                        ) : (
                            <Moon className="w-4 h-4" />
                        )}
                    </button>
                    <button
                        onClick={logout}
                        className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        title="Sign out"
                    >
                        <LogOut className="w-4 h-4" />
                    </button>
                </div>
            </div>
        </div>
    );
}
