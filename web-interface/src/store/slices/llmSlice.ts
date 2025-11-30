import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface LLMModel {
  name: string;
  provider: string;
  cost_per_token: {
    input: number;
    output: number;
  };
  requests_count: number;
  total_cost: number;
  avg_response_time: number;
}

export interface LLMProvider {
  name: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  models: LLMModel[];
  current_load: number;
  max_requests: number;
  total_requests: number;
  total_cost: number;
}

export interface LLMMetrics {
  total_requests: number;
  total_cost: number;
  avg_response_time: number;
  requests_by_model: Record<string, number>;
  cost_by_provider: Record<string, number>;
}

export interface LLMState {
  providers: LLMProvider[];
  metrics: LLMMetrics;
  selectedProvider: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: LLMState = {
  providers: [],
  metrics: {
    total_requests: 0,
    total_cost: 0,
    avg_response_time: 0,
    requests_by_model: {},
    cost_by_provider: {},
  },
  selectedProvider: null,
  loading: false,
  error: null,
};

const llmSlice = createSlice({
  name: 'llm',
  initialState,
  reducers: {
    setProviders: (state, action: PayloadAction<LLMProvider[]>) => {
      state.providers = action.payload;
    },
    updateMetrics: (state, action: PayloadAction<LLMMetrics>) => {
      state.metrics = action.payload;
    },
    selectProvider: (state, action: PayloadAction<string | null>) => {
      state.selectedProvider = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    updateProviderStatus: (state, action: PayloadAction<{
      providerName: string;
      status: LLMProvider['status'];
      metrics?: Partial<LLMProvider>;
    }>) => {
      const provider = state.providers.find(p => p.name === action.payload.providerName);
      if (provider) {
        provider.status = action.payload.status;
        if (action.payload.metrics) {
          Object.assign(provider, action.payload.metrics);
        }
      }
    },
  },
});

export const {
  setProviders,
  updateMetrics,
  selectProvider,
  setLoading,
  setError,
  updateProviderStatus,
} = llmSlice.actions;

export default llmSlice.reducer;