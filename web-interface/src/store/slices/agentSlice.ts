import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface Agent {
  name: string;
  agent_type: string;
  endpoint: string;
  capabilities: Array<{
    name: string;
    description: string;
    tools: string[];
    confidence_level: number;
  }>;
  health_status: 'healthy' | 'warning' | 'error' | 'unknown';
  last_health_check?: string;
  load_factor: number;
  active_tasks: number;
  total_requests: number;
  avg_response_time: number;
}

export interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

const initialState: AgentState = {
  agents: [],
  selectedAgent: null,
  loading: false,
  error: null,
  lastUpdated: null,
};

// Async thunks
export const fetchAgents = createAsyncThunk(
  'agents/fetchAgents',
  async () => {
    const response = await fetch('/api/agents');
    if (!response.ok) {
      throw new Error('Failed to fetch agents');
    }
    return response.json();
  }
);

export const fetchAgentHealth = createAsyncThunk(
  'agents/fetchAgentHealth',
  async (agentEndpoint: string) => {
    const response = await fetch(`${agentEndpoint}/health`);
    if (!response.ok) {
      throw new Error('Failed to fetch agent health');
    }
    return { endpoint: agentEndpoint, health: await response.json() };
  }
);

const agentSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    selectAgent: (state, action: PayloadAction<Agent | null>) => {
      state.selectedAgent = action.payload;
    },
    updateAgentStatus: (state, action: PayloadAction<{
      endpoint: string;
      status: Agent['health_status'];
      metrics?: Partial<Agent>;
    }>) => {
      const agent = state.agents.find(a => a.endpoint === action.payload.endpoint);
      if (agent) {
        agent.health_status = action.payload.status;
        agent.last_health_check = new Date().toISOString();
        if (action.payload.metrics) {
          Object.assign(agent, action.payload.metrics);
        }
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAgents.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAgents.fulfilled, (state, action) => {
        state.loading = false;
        state.agents = action.payload.agents || [];
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchAgents.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch agents';
      })
      .addCase(fetchAgentHealth.fulfilled, (state, action) => {
        const agent = state.agents.find(a => a.endpoint === action.payload.endpoint);
        if (agent) {
          agent.health_status = action.payload.health.status === 'healthy' ? 'healthy' : 'error';
          agent.last_health_check = new Date().toISOString();
        }
      });
  },
});

export const { selectAgent, updateAgentStatus, clearError } = agentSlice.actions;
export default agentSlice.reducer;