import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { MessageSquarePlus, Trash2, LogOut, User, Sun, Moon, PanelLeftClose } from 'lucide-react';
import type { ChatSession } from '../types';

interface SidebarProps {
    sessions: ChatSession[];
    activeSession: ChatSession | null;
    onSelectSession: (session: ChatSession) => void;
    onNewChat: () => void;
    onDeleteSession: (sessionId: string) => void;
    isOpen: boolean;
    onToggle: () => void;
    isLoading?: boolean;
}

export default function Sidebar({
    sessions,
    activeSession,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    isOpen,
    onToggle,
    isLoading = false
}: SidebarProps) {
    const { user, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const [deleteConfirmation, setDeleteConfirmation] = useState<{ isOpen: boolean; sessionId: string | null }>({
        isOpen: false,
        sessionId: null
    });

    if (!isOpen) return null;

    return (
        <div className="w-64 bg-white dark:bg-slate-950 flex flex-col border-r border-slate-200 dark:border-slate-800">
            {/* Header: Project Name & Toggle */}
            <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Foundry Chat
                </h1>
                <button
                    onClick={onToggle}
                    className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 dark:text-slate-400 transition-colors"
                >
                    <PanelLeftClose className="w-5 h-5" />
                </button>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 mb-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg transition-all shadow-sm group"
                >
                    <MessageSquarePlus className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    <span className="font-medium">New Chat</span>
                </button>

                {isLoading ? (
                    // Skeleton Loader
                    [...Array(5)].map((_, i) => (
                        <div key={i} className="px-3 py-2 animate-pulse">
                            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
                        </div>
                    ))
                ) : sessions.length === 0 ? (
                    <div className="text-center py-4 text-slate-500 dark:text-slate-500 text-sm">
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
                                    setDeleteConfirmation({ isOpen: true, sessionId: session.id });
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
            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
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

            {/* Delete Confirmation Modal */}
            {deleteConfirmation.isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-sm p-6 shadow-xl border border-slate-200 dark:border-slate-800 animate-in fade-in zoom-in-95 duration-200">
                        <div className="flex flex-col items-center text-center gap-4">
                            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                                <Trash2 className="w-6 h-6 text-red-600 dark:text-red-500" />
                            </div>
                            <div className="space-y-1">
                                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Delete Chat?</h3>
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    This will permanently delete this conversation.
                                </p>
                            </div>
                            <div className="flex gap-3 w-full mt-2">
                                <button
                                    onClick={() => setDeleteConfirmation({ isOpen: false, sessionId: null })}
                                    className="flex-1 px-4 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl font-medium transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => {
                                        if (deleteConfirmation.sessionId) {
                                            onDeleteSession(deleteConfirmation.sessionId);
                                        }
                                        setDeleteConfirmation({ isOpen: false, sessionId: null });
                                    }}
                                    className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors shadow-sm shadow-red-500/20"
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
