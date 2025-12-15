import axios, { AxiosInstance } from 'axios';
import { apiConfig } from '../config/azureConfig';
import type {
  User,
  Agent,
  AgentResponse,
  ChatSession,
  CreateSessionRequest,
  SendMessageRequest,
  MessageResponse,
  SessionResponse,
  ChatHistoryResponse,
} from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: apiConfig.baseUrl,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setAuthToken(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearAuthToken() {
    delete this.client.defaults.headers.common['Authorization'];
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  async getAgents(): Promise<AgentResponse> {
    const response = await this.client.get<AgentResponse>('/agents');
    return response.data;
  }

  async getAgent(agentId: string): Promise<Agent> {
    const response = await this.client.get<Agent>(`/agents/${agentId}`);
    return response.data;
  }

  async createSession(request: CreateSessionRequest): Promise<SessionResponse> {
    const response = await this.client.post<SessionResponse>('/sessions', request);
    return response.data;
  }

  async getUserSessions(): Promise<ChatSession[]> {
    const response = await this.client.get<ChatSession[]>('/sessions');
    return response.data;
  }

  async getSessionHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await this.client.get<ChatHistoryResponse>(`/sessions/${sessionId}`);
    return response.data;
  }

  async sendMessage(request: SendMessageRequest): Promise<MessageResponse> {
    const response = await this.client.post<MessageResponse>('/chat', request);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.client.delete(`/sessions/${sessionId}`);
  }

  async healthCheck(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();
