import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LogIn, MessageSquare, Shield, Zap } from 'lucide-react';

const Login: React.FC = () => {
  const { login, isLoading, error } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-6xl w-full grid md:grid-cols-2 gap-8 items-center">
        <div className="text-white space-y-6 px-4 md:px-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-12 h-12 text-blue-400" />
              <h1 className="text-4xl md:text-5xl font-bold">Azure AI Chat</h1>
            </div>
            <p className="text-xl text-slate-300">
              Connect with intelligent AI agents powered by Azure Foundry
            </p>
          </div>

          <div className="space-y-4 pt-8">
            <div className="flex items-start gap-4">
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <Shield className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Secure Authentication</h3>
                <p className="text-slate-400">
                  Enterprise-grade security with Azure Entra ID
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <Zap className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Intelligent Agents</h3>
                <p className="text-slate-400">
                  Access powerful AI agents from Azure Foundry
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="bg-blue-500/20 p-3 rounded-lg">
                <MessageSquare className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Seamless Experience</h3>
                <p className="text-slate-400">
                  Chat naturally with context-aware AI assistants
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-12 space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-slate-900">Welcome</h2>
            <p className="text-slate-600">Sign in to start chatting with AI agents</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              <p className="text-sm">{error}</p>
            </div>
          )}

          <button
            onClick={login}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <LogIn className="w-5 h-5" />
                <span>Sign in with Microsoft</span>
              </>
            )}
          </button>

          <div className="text-center text-sm text-slate-500">
            <p>By signing in, you agree to our Terms of Service and Privacy Policy</p>
          </div>

          <div className="pt-6 border-t border-slate-200">
            <div className="text-center text-xs text-slate-500 space-y-1">
              <p>Powered by Azure Entra ID & Azure Foundry</p>
              <p>OAuth Identity Passthrough (MCP) Enabled</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
