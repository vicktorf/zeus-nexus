import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Task {
  id: string;
  request_id: string;
  agent_type: string;
  agent_endpoint: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error?: string;
  started_at?: string;
  completed_at?: string;
  execution_time_ms?: number;
  user_id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface TaskState {
  tasks: Task[];
  selectedTask: Task | null;
  loading: boolean;
  error: string | null;
  filters: {
    status?: Task['status'];
    agent_type?: string;
    priority?: Task['priority'];
  };
}

const initialState: TaskState = {
  tasks: [],
  selectedTask: null,
  loading: false,
  error: null,
  filters: {},
};

const taskSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    setTasks: (state, action: PayloadAction<Task[]>) => {
      state.tasks = action.payload;
    },
    addTask: (state, action: PayloadAction<Task>) => {
      state.tasks.unshift(action.payload);
    },
    updateTask: (state, action: PayloadAction<{
      id: string;
      updates: Partial<Task>;
    }>) => {
      const taskIndex = state.tasks.findIndex(t => t.id === action.payload.id);
      if (taskIndex !== -1) {
        state.tasks[taskIndex] = {
          ...state.tasks[taskIndex],
          ...action.payload.updates,
        };
      }
    },
    selectTask: (state, action: PayloadAction<Task | null>) => {
      state.selectedTask = action.payload;
    },
    setFilters: (state, action: PayloadAction<TaskState['filters']>) => {
      state.filters = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    removeTask: (state, action: PayloadAction<string>) => {
      state.tasks = state.tasks.filter(t => t.id !== action.payload);
    },
  },
});

export const {
  setTasks,
  addTask,
  updateTask,
  selectTask,
  setFilters,
  setLoading,
  setError,
  removeTask,
} = taskSlice.actions;

export default taskSlice.reducer;