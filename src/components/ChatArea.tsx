import { useState, useEffect, useRef } from 'react';
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
}

export default function ChatArea({
    selectedAgent,
    agents,
    activeSession,
    onAgentChange,
    onNewChat,
    onSessionCreated,
    sidebarOpen,
    onToggleSidebar
}: ChatAreaProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch messages when active session changes
    useEffect(() => {
        if (activeSession) {
            fetchMessages();
        } else {
            setMessages([]);
        }
    }, [activeSession]);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchMessages = async () => {
        if (!activeSession) return;

        try {
            const response = await api.getSessionHistory(activeSession.id);
            setMessages(response.messages || []);
        } catch (error) {
            console.error('Failed to fetch messages:', error);
            // Set empty messages on error to prevent crash
            setMessages([]);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || !selectedAgent || loading) return;

        // Create session if none exists
        let sessionId = activeSession?.id;
        if (!sessionId) {
            try {
                const response = await api.createSession({
                    agent_id: selectedAgent.id,
                    title: input.slice(0, 50) // Use first 50 chars as title
                });
                sessionId = response.session.id;
                onSessionCreated(response.session); // Update active session in layout
            } catch (error) {
                console.error('Failed to create session:', error);
                return;
            }
        }

        const userMessage = input;
        setInput('');
        setLoading(true);

        // Add user message to UI immediately
        const tempUserMessage: ChatMessage = {
            id: Date.now().toString(),
            session_id: sessionId!,
            role: 'user',
            content: userMessage,
            metadata: {},
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempUserMessage]);

        try {
            const response = await api.sendMessage({
                session_id: sessionId!,
                content: userMessage,
                metadata: {}
            });

            // Replace temp message with actual message and add assistant response
            setMessages(prev => [
                ...prev.filter(m => m.id !== tempUserMessage.id),
                { ...tempUserMessage, id: response.message.id },
                response.message
            ]);
        } catch (error) {
            console.error('Failed to send message:', error);
            // Remove temp message on error
            setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id));
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 transition-colors duration-200">
            {/* Header with Agent Dropdown */}
            <div className="h-14 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
                <div className="flex items-center gap-3">
                    {!sidebarOpen && (
                        <button
                            onClick={onToggleSidebar}
                            className="p-2 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        >
                            <Menu className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                        </button>
                    )}

                    {/* Agent Dropdown */}
                    <div className="relative">
                        <button
                            onClick={() => setAgentDropdownOpen(!agentDropdownOpen)}
                            className="flex items-center gap-2 px-4 py-2 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 rounded-lg transition-colors text-slate-900 dark:text-white"
                        >
                            <Bot className="w-5 h-5" />
                            <span className="font-medium">
                                {selectedAgent?.name || 'Select Agent'}
                            </span>
                            <ChevronDown className="w-4 h-4" />
                        </button>

                        {/* Dropdown Menu */}
                        {agentDropdownOpen && (
                            <div className="absolute top-full left-0 mt-2 w-64 bg-white dark:bg-slate-800 rounded-lg shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-50">
                                {agents.map((agent) => (
                                    <button
                                        key={agent.id}
                                        onClick={() => {
                                            onAgentChange(agent);
                                            setAgentDropdownOpen(false);
                                        }}
                                        className={`w-full text-left px-4 py-3 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${selectedAgent?.id === agent.id ? 'bg-slate-100 dark:bg-slate-700' : ''
                                            }`}
                                    >
                                        <div className="font-medium text-slate-900 dark:text-white">{agent.name}</div>
                                        {agent.description && (
                                            <div className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                                {agent.description}
                                            </div>
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* New Chat Button */}
                <button
                    onClick={onNewChat}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                >
                    New Chat
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto">
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-slate-500">
                        <div className="text-center space-y-3">
                            <Bot className="w-16 h-16 mx-auto text-slate-400 dark:text-slate-600" />
                            <p className="text-lg font-medium text-slate-700 dark:text-slate-300">Start a conversation</p>
                            <p className="text-sm">
                                {selectedAgent
                                    ? `Ask ${selectedAgent.name} anything`
                                    : 'Select an agent to begin'}
                            </p>
                        </div>
                    </div>
                ) : (
                    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'
                                    }`}
                            >
                                {message.role === 'assistant' && (
                                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                )}

                                <div
                                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${message.role === 'user'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                                        }`}
                                >
                                    <p className="whitespace-pre-wrap">{message.content}</p>
                                </div>

                                {message.role === 'user' && (
                                    <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center flex-shrink-0">
                                        <span className="text-slate-900 dark:text-white text-sm font-medium">You</span>
                                    </div>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="flex gap-4">
                                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                                    <Bot className="w-5 h-5 text-white" />
                                </div>
                                <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl px-4 py-3">
                                    <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="border-t border-slate-200 dark:border-slate-800 p-4 bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
                <div className="max-w-3xl mx-auto">
                    <div className="flex gap-3 items-end">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={
                                selectedAgent
                                    ? `Message ${selectedAgent.name}...`
                                    : 'Select an agent first...'
                            }
                            disabled={!selectedAgent || loading}
                            className="flex-1 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl px-4 py-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-600 disabled:opacity-50 disabled:cursor-not-allowed border border-slate-200 dark:border-slate-700 placeholder-slate-400 dark:placeholder-slate-500"
                            rows={1}
                            style={{
                                minHeight: '48px',
                                maxHeight: '200px'
                            }}
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || !selectedAgent || loading}
                            className="p-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 dark:disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
