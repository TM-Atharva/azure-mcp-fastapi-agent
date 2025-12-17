import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Menu, ChevronDown, Bot, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { Agent, ChatSession, ChatMessage } from '../types';

interface ChatAreaProps {
    selectedAgent: Agent | null;
    agents: Agent[];
    activeSession: ChatSession | null;
    onAgentChange: (agent: Agent) => void;
    onNewChat: () => void;
    onSessionCreated: (session: ChatSession) => void;
    sidebarOpen: boolean;
    onToggleSidebar: () => void;
    isLoadingAgents?: boolean;
}

export default function ChatArea({
    selectedAgent,
    agents,
    activeSession,
    onAgentChange,
    onNewChat,
    onSessionCreated,
    sidebarOpen,
    onToggleSidebar,
    isLoadingAgents = false
}: ChatAreaProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);

    // Use a ref for the scroll anchor
    const messagesEndRef = useRef<HTMLDivElement>(null);
    // Use a ref to skip fetch after creating a session (prevents wiping optimistic state)
    const skipNextFetchRef = useRef(false);
    // Use a ref to track the last rendered session ID to detect switches
    const lastSessionIdRef = useRef<string | undefined>(activeSession?.id);

    // Derived state: Are we in the process of switching sessions?
    // We ignore this if we are in the "skip fetch" (creation) mode.
    const isSwitchingSession = activeSession?.id &&
        activeSession.id !== lastSessionIdRef.current &&
        !skipNextFetchRef.current;

    // Initial fetch when session changes
    useEffect(() => {
        let isMounted = true;

        if (skipNextFetchRef.current) {
            skipNextFetchRef.current = false;
            // Sync the ref immediately since we are skipping the fetch logic
            lastSessionIdRef.current = activeSession?.id;
            return;
        }

        const loadMessages = async () => {
            if (activeSession) {
                setLoading(true);
                // Note: We don't strictly need to clear messages here if we use isSwitchingSession
                // but it's good practice.
                setMessages([]);

                try {
                    const response = await api.getSessionHistory(activeSession.id);
                    if (isMounted) {
                        setMessages(response.messages || []);
                        // Sync the ref now that we have data
                        lastSessionIdRef.current = activeSession.id;
                    }
                } catch (error) {
                    console.error('Failed to fetch messages:', error);
                    if (isMounted) {
                        setMessages([]);
                        lastSessionIdRef.current = activeSession.id;
                    }
                } finally {
                    if (isMounted) setLoading(false);
                }
            } else {
                if (isMounted) {
                    setMessages([]);
                    lastSessionIdRef.current = activeSession?.id; // Sync for new chat (null)
                }
            }
        };

        loadMessages();

        return () => {
            isMounted = false;
        };
    }, [activeSession?.id]);

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const handleSend = async () => {
        if (!input.trim() || !selectedAgent || loading) return;

        const userMessageContent = input;
        setInput(''); // Clear input immediately

        let currentSessionId = activeSession?.id;

        // Optimistic update: Add user message locally
        const tempId = Date.now().toString();
        const tempUserMessage: ChatMessage = {
            id: tempId,
            session_id: currentSessionId || 'temp',
            role: 'user',
            content: userMessageContent,
            metadata: {},
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMessage]);
        setLoading(true);

        try {
            // If no active session, create one first
            if (!currentSessionId) {
                try {
                    const sessionResponse = await api.createSession({
                        agent_id: selectedAgent.id,
                        title: userMessageContent.slice(0, 50)
                    });
                    currentSessionId = sessionResponse.session.id;
                    // Notify parent to update sidebar, but we handle state locally mostly
                    skipNextFetchRef.current = true;
                    onSessionCreated(sessionResponse.session);
                } catch (error) {
                    console.error('Failed to create session:', error);
                    // Remove optimistic message if session creation fails
                    setMessages(prev => prev.filter(m => m.id !== tempId));
                    setLoading(false);
                    return;
                }
            }

            // Send message
            const response = await api.sendMessage({
                session_id: currentSessionId!,
                content: userMessageContent,
                metadata: {}
            });

            // Replace optimistic message with real one and add assistant response
            setMessages(prev => {
                const filtered = prev.filter(m => m.id !== tempId);
                return [
                    ...filtered,
                    { ...tempUserMessage, id: response.message.id, session_id: currentSessionId! }, // Update with real ID
                    response.message
                ];
            });

        } catch (error) {
            console.error('Failed to send message:', error);
            // Remove optimistic message on error
            setMessages(prev => prev.filter(m => m.id !== tempId));
            alert('Failed to send message. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Close dropdown when clicking outside (simple version)
    useEffect(() => {
        const handleClickOutside = () => setAgentDropdownOpen(false);
        if (agentDropdownOpen) {
            document.addEventListener('click', handleClickOutside);
        }
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [agentDropdownOpen]);

    return (
        <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-900 transition-colors duration-200 h-screen overflow-hidden">
            {/* Header */}
            <div className="flex-none h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex items-center justify-between px-4 z-10 shadow-sm">
                <div className="flex items-center gap-3">
                    {!sidebarOpen && (
                        <button
                            onClick={onToggleSidebar}
                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-500 dark:text-slate-400"
                        >
                            <Menu className="w-5 h-5" />
                        </button>
                    )}

                    {/* Agent Selector */}
                    <div className="relative" onClick={e => e.stopPropagation()}>
                        <button
                            onClick={() => !isLoadingAgents && setAgentDropdownOpen(!agentDropdownOpen)}
                            className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md transition-colors text-slate-900 dark:text-slate-100 font-medium text-sm disabled:opacity-50 disabled:cursor-wait"
                            disabled={isLoadingAgents}
                        >
                            {isLoadingAgents ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin text-blue-600 dark:text-blue-400" />
                                    <span>Loading Agents...</span>
                                </>
                            ) : (
                                <>
                                    <Bot className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                                    <span>{selectedAgent?.name || 'Select Agent'}</span>
                                    <ChevronDown className="w-4 h-4 text-slate-500" />
                                </>
                            )}
                        </button>

                        {/* Dropdown */}
                        {agentDropdownOpen && (
                            <div className="absolute top-full left-0 mt-2 w-72 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-1 overflow-hidden z-50">
                                {agents.map((agent) => (
                                    <button
                                        key={agent.id}
                                        onClick={() => {
                                            onAgentChange(agent);
                                            setAgentDropdownOpen(false);
                                        }}
                                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-start gap-3 ${selectedAgent?.id === agent.id ? 'bg-slate-50 dark:bg-slate-700/50' : ''
                                            }`}
                                    >
                                        <div className="mt-1">
                                            <Bot className="w-8 h-8 p-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg" />
                                        </div>
                                        <div>
                                            <div className="font-medium text-slate-900 dark:text-slate-100 text-sm">{agent.name}</div>
                                            {agent.description && (
                                                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                                                    {agent.description}
                                                </div>
                                            )}
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* New Chat Button Removed as per request */}
                </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto min-h-0 bg-white dark:bg-slate-900 scroll-smooth">
                {isSwitchingSession || (messages.length === 0 && loading) ? (
                    // Skeleton Loader for Session Switch
                    <div className="h-full max-w-3xl mx-auto px-4 py-8 space-y-6">
                        <div className="flex justify-center mb-8">
                            <span className="text-sm text-slate-400 animate-pulse">Loading conversation...</span>
                        </div>
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className={`flex gap-4 ${i % 2 === 0 ? 'justify-start' : 'justify-end'} animate-pulse opacity-50`}>
                                <div className={`h-16 rounded-2xl w-[70%] ${i % 2 === 0 ? 'bg-slate-100 dark:bg-slate-800' : 'bg-slate-200 dark:bg-slate-700'}`}></div>
                            </div>
                        ))}
                    </div>
                ) : !activeSession && messages.length === 0 ? (
                    // Empty State (New Chat)
                    <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-500 dark:text-slate-400">
                        <div className="w-20 h-20 bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-6">
                            <Bot className="w-10 h-10 text-slate-400 dark:text-slate-500" />
                        </div>
                        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-2">
                            {selectedAgent ? `Chat with ${selectedAgent.name}` : 'Start a new conversation'}
                        </h2>
                        <p className="max-w-md mx-auto mb-8">
                            {selectedAgent
                                ? selectedAgent.description
                                : 'Select an agent from the dropdown to begin exploring their capabilities.'}
                        </p>
                    </div>
                ) : (
                    // Message List
                    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                {/* Assistant Avatar */}
                                {message.role === 'assistant' && (
                                    <div className="w-8 h-8 bg-blue-600 dark:bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                )}

                                {/* Message Bubble */}
                                <div
                                    className={`relative max-w-[85%] rounded-2xl px-5 py-3 shadow-sm ${message.role === 'user'
                                        ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-br-none'
                                        : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-100 dark:border-slate-700 rounded-bl-none'
                                        }`}
                                >
                                    <div className="prose prose-slate dark:prose-invert max-w-none leading-relaxed text-[15px]">
                                        <ReactMarkdown>{message.content}</ReactMarkdown>
                                    </div>
                                </div>

                                {/* User Avatar */}
                                {message.role === 'user' && (
                                    <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                                        <span className="text-xs font-medium text-slate-600 dark:text-slate-300">You</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Bottom Loading Indicator (for sending) */}
                {loading && !isSwitchingSession && messages.length > 0 && (
                    <div className="max-w-3xl mx-auto px-4 pb-4">
                        <div className="flex gap-4">
                            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm mt-1">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div className="bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
                                <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                            </div>
                        </div>
                    </div>
                )}
                {messages.length > 0 && <div ref={messagesEndRef} className="h-4" />}
            </div>
            {/* Input Area */}
            <div className="flex-none p-4 bg-white dark:bg-slate-950">
                <div className="max-w-3xl mx-auto relative">
                    <div className="relative flex items-end gap-2 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm focus-within:ring-2 focus-within:ring-blue-500/50 transition-all">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={e => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder={selectedAgent ? `Message ${selectedAgent.name}...` : 'Select an agent to start...'}
                            disabled={!selectedAgent || loading}
                            className="w-full bg-transparent text-slate-900 dark:text-white rounded-xl pl-4 pr-12 py-3.5 focus:outline-none resize-none placeholder:text-slate-400"
                            rows={1}
                            style={{ minHeight: '52px', maxHeight: '200px' }}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || !selectedAgent || loading}
                            className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors shadow-sm"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="text-center mt-2">
                        <p className="text-xs text-slate-400 dark:text-slate-500">
                            AI agents can make mistakes. Verify important information.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
