import { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Login';
import AgentSelection from './components/AgentSelection';
import Chat from './components/Chat';
import { LogOut, Loader2 } from 'lucide-react';
import type { Agent } from './types';

function AppContent() {
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgent(agent);
  };

  const handleBackToAgents = () => {
    setSelectedAgent(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto" />
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="relative">
      {!selectedAgent && (
        <div className="absolute top-4 right-4 z-10 flex items-center gap-3">
          <div className="hidden md:block text-right">
            <p className="text-sm font-medium text-slate-900">{user?.name}</p>
            <p className="text-xs text-slate-600">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="bg-white hover:bg-slate-100 text-slate-700 p-2 rounded-lg shadow-md transition-colors flex items-center gap-2"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden md:inline text-sm">Sign Out</span>
          </button>
        </div>
      )}

      {selectedAgent ? (
        <Chat agent={selectedAgent} onBack={handleBackToAgents} />
      ) : (
        <AgentSelection onSelectAgent={handleSelectAgent} />
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
