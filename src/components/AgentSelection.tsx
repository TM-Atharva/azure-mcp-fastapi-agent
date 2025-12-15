import React, { useEffect, useState } from "react";
import {
  Bot,
  ChevronRight,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { apiClient } from "../services/api";
import type { Agent } from "../types";

interface AgentSelectionProps {
  onSelectAgent: (agent: Agent) => void;
}

const AgentSelection: React.FC<AgentSelectionProps> = ({ onSelectAgent }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getAgents();
      setAgents(response.agents);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load agents");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectAgent = (agent: Agent) => {
    setSelectedAgentId(agent.id);
    onSelectAgent(agent);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto" />
          <p className="text-slate-600">Loading AI agents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-semibold text-slate-900">
            Failed to Load Agents
          </h2>
          <p className="text-slate-600">{error}</p>
          <button
            onClick={loadAgents}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-8 md:py-12">
        <div className="text-center space-y-4 mb-12">
          <div className="flex items-center justify-center gap-3">
            <Sparkles className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900">
              Choose Your AI Agent
            </h1>
          </div>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Select an AI agent to start your conversation. Each agent has unique
            capabilities powered by Azure Foundry.
          </p>
        </div>

        {agents.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <Bot className="w-16 h-16 text-slate-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              No Agents Available
            </h3>
            <p className="text-slate-600">
              No AI agents are currently configured in your Azure Foundry
              project.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <div
                key={agent.id}
                onClick={() => handleSelectAgent(agent)}
                className={`bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer overflow-hidden group ${
                  selectedAgentId === agent.id ? "ring-2 ring-blue-600" : ""
                }`}
              >
                <div className="p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-3 rounded-lg">
                      <Bot className="w-6 h-6 text-white" />
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {agent.name}
                    </h3>
                    <p className="text-slate-600 text-sm line-clamp-3">
                      {agent.description ||
                        "An intelligent AI assistant ready to help you."}
                    </p>
                    {agent.capabilities?.deployment_model_name && (
                      <p className="text-sm text-slate-700 font-medium mt-2">
                        Model:{" "}
                        <span className="text-blue-600">
                          {agent.capabilities.deployment_model_name}
                        </span>
                      </p>
                    )}
                  </div>

                  {agent.capabilities &&
                    Object.keys(agent.capabilities).length > 0 && (
                      <div className="pt-4 border-t border-slate-100">
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(agent.capabilities)
                            .slice(0, 3)
                            .map(([key]) => (
                              <span
                                key={key}
                                className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                              >
                                {key.replace(/_/g, " ")}
                              </span>
                            ))}
                        </div>
                      </div>
                    )}

                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg transition-colors font-medium">
                    Start Chatting
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentSelection;
