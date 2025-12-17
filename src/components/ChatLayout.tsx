import { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import ChatArea from './ChatArea';
import { api } from '../services/api';
import type { Agent, ChatSession } from '../types';

export default function ChatLayout() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [loadingAgents, setLoadingAgents] = useState(true);

    // Fetch agents on mount
    useEffect(() => {
        const init = async () => {
            await Promise.all([fetchAgents(), fetchSessions()]);
        };
        init();
    }, []);

    const fetchAgents = async () => {
        try {
            setLoadingAgents(true);
            const response = await api.getAgents();
            setAgents(response.agents);

            // Auto-select first agent if none selected
            if (response.agents.length > 0 && !selectedAgent) {
                setSelectedAgent(response.agents[0]);
            }
        } catch (error) {
            console.error('Failed to fetch agents:', error);
        } finally {
            setLoadingAgents(false);
        }
    };

    const fetchSessions = async () => {
        try {
            setLoadingSessions(true);
            const sessions = await api.getSessions();
            setSessions(sessions);
        } catch (error) {
            console.error('Failed to fetch sessions:', error);
        } finally {
            setLoadingSessions(false);
        }
    };

    const handleNewChat = async () => {
        setActiveSession(null);
    };

    const handleSessionCreated = (session: ChatSession) => {
        setSessions([session, ...sessions]);
        setActiveSession(session);
    };

    const handleSelectSession = (session: ChatSession) => {
        setActiveSession(session);

        // Find and set the agent for this session
        const agent = agents.find(a => String(a.id) === String(session.agent_id));
        if (agent) {
            setSelectedAgent(agent);
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        try {
            await api.deleteSession(sessionId);
            setSessions(sessions.filter(s => s.id !== sessionId));

            // If deleted session was active, clear it
            if (activeSession?.id === sessionId) {
                setActiveSession(null);
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const handleAgentChange = (agent: Agent) => {
        setSelectedAgent(agent);
        // Clear active session when changing agents
        setActiveSession(null);
    };

    return (
        <div className="flex h-screen bg-white dark:bg-slate-900 transition-colors duration-200">
            {/* Sidebar */}
            <Sidebar
                sessions={sessions}
                activeSession={activeSession}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
                isOpen={sidebarOpen}
                onToggle={() => setSidebarOpen(!sidebarOpen)}
                isLoading={loadingSessions || loadingAgents}
            />

            {/* Main Chat Area */}
            <ChatArea
                selectedAgent={selectedAgent}
                agents={agents}
                activeSession={activeSession}
                onAgentChange={handleAgentChange}
                onNewChat={handleNewChat}
                onSessionCreated={handleSessionCreated}
                sidebarOpen={sidebarOpen}
                onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
                isLoadingAgents={loadingAgents}
            />
        </div>
    );
}
