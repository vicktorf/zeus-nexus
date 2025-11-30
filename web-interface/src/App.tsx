import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ChatInterface from './pages/Chat/ChatInterface';
import AgentManager from './pages/Agents/AgentManager';
import LLMMonitor from './pages/LLM/LLMMonitor';
import TaskTracker from './pages/Tasks/TaskTracker';
import Settings from './pages/Settings/Settings';

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<ChatInterface />} />
          <Route path="/agents" element={<AgentManager />} />
          <Route path="/llm" element={<LLMMonitor />} />
          <Route path="/tasks" element={<TaskTracker />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;