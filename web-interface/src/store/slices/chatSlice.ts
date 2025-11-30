import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  agent?: string;
  status?: 'sending' | 'sent' | 'error';
  metadata?: {
    reasoning?: string;
    confidence?: number;
    execution_time?: number;
    agent_used?: string;
    cost?: number;
  };
}

export interface ChatState {
  messages: ChatMessage[];
  isTyping: boolean;
  currentAgent: string | null;
  sessionId: string | null;
  connectionStatus: 'connected' | 'disconnected' | 'connecting';
}

const initialState: ChatState = {
  messages: [
    {
      id: '1',
      type: 'system',
      content: 'Xin chào! Tôi là Zeus - trợ lý AI thông minh. Tôi có thể giúp bạn với quản lý dự án, kiến trúc cloud, tư vấn kinh doanh và nhiều tác vụ khác. Bạn cần hỗ trợ gì?',
      timestamp: new Date().toISOString(),
    }
  ],
  isTyping: false,
  currentAgent: null,
  sessionId: null,
  connectionStatus: 'disconnected',
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<Omit<ChatMessage, 'id' | 'timestamp'>>) => {
      const message: ChatMessage = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
      };
      state.messages.push(message);
    },
    updateMessage: (state, action: PayloadAction<{
      id: string;
      updates: Partial<ChatMessage>;
    }>) => {
      const messageIndex = state.messages.findIndex(m => m.id === action.payload.id);
      if (messageIndex !== -1) {
        state.messages[messageIndex] = {
          ...state.messages[messageIndex],
          ...action.payload.updates,
        };
      }
    },
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.isTyping = action.payload;
    },
    setCurrentAgent: (state, action: PayloadAction<string | null>) => {
      state.currentAgent = action.payload;
    },
    setSessionId: (state, action: PayloadAction<string>) => {
      state.sessionId = action.payload;
    },
    setConnectionStatus: (state, action: PayloadAction<ChatState['connectionStatus']>) => {
      state.connectionStatus = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [initialState.messages[0]]; // Keep welcome message
    },
    deleteMessage: (state, action: PayloadAction<string>) => {
      state.messages = state.messages.filter(m => m.id !== action.payload);
    },
  },
});

export const {
  addMessage,
  updateMessage,
  setTyping,
  setCurrentAgent,
  setSessionId,
  setConnectionStatus,
  clearMessages,
  deleteMessage,
} = chatSlice.actions;

export default chatSlice.reducer;