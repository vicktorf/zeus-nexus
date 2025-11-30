import { configureStore } from '@reduxjs/toolkit';
import agentSlice from './slices/agentSlice';
import chatSlice from './slices/chatSlice';
import llmSlice from './slices/llmSlice';
import taskSlice from './slices/taskSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    agents: agentSlice,
    chat: chatSlice,
    llm: llmSlice,
    tasks: taskSlice,
    ui: uiSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;