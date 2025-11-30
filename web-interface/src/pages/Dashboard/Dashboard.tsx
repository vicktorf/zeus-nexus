import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Avatar,
  Chip,
  LinearProgress,
  IconButton,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  Speed,
  Memory,
  Cloud,
  Security,
  Analytics,
  Refresh,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const Dashboard: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState({
    totalRequests: 1247,
    avgResponseTime: 342,
    successRate: 98.5,
    activeTasks: 23,
    totalCost: 45.67,
    uptime: 99.9,
  });

  const [agentStatus] = useState([
    { name: 'Athena', status: 'healthy', load: 65, requests: 342, icon: '📋' },
    { name: 'Hephaestus', status: 'healthy', load: 78, requests: 234, icon: '☁️' },
    { name: 'Apollo', status: 'healthy', load: 45, requests: 156, icon: '💼' },
    { name: 'Hermes', status: 'warning', load: 89, requests: 278, icon: '💰' },
    { name: 'Vulcan', status: 'healthy', load: 56, requests: 198, icon: '⚙️' },
    { name: 'Ares', status: 'healthy', load: 34, requests: 89, icon: '🛡️' },
  ]);

  const performanceData = [
    { time: '00:00', requests: 45, responseTime: 320 },
    { time: '04:00', requests: 23, responseTime: 280 },
    { time: '08:00', requests: 89, responseTime: 350 },
    { time: '12:00', requests: 156, responseTime: 420 },
    { time: '16:00', requests: 234, responseTime: 380 },
    { time: '20:00', requests: 198, responseTime: 340 },
  ];

  const llmUsageData = [
    { name: 'GPT-4', value: 45, color: '#667eea' },
    { name: 'Claude-3', value: 30, color: '#764ba2' },
    { name: 'Local LLM', value: 25, color: '#4caf50' },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#4caf50';
      case 'warning': return '#ff9800';
      case 'error': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const MetricCard = ({ title, value, change, icon, color }: any) => (
    <Card className="metric-card">
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ color }}>
              {value}
            </Typography>
            {change && (
              <Typography variant="body2" color={change > 0 ? 'success.main' : 'error.main'}>
                {change > 0 ? '+' : ''}{change}% từ hôm qua
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, opacity: 0.8 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          📊 Zeus Nexus Dashboard
        </Typography>
        <IconButton color="primary">
          <Refresh />
        </IconButton>
      </Box>

      {/* System Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Total Requests"
            value={systemMetrics.totalRequests.toLocaleString()}
            change={12.5}
            icon={<TrendingUp />}
            color="#667eea"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Avg Response Time"
            value={`${systemMetrics.avgResponseTime}ms`}
            change={-8.2}
            icon={<Speed />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Success Rate"
            value={`${systemMetrics.successRate}%`}
            change={0.3}
            icon={<Analytics />}
            color="#2196f3"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Active Tasks"
            value={systemMetrics.activeTasks}
            change={15.7}
            icon={<Memory />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Total Cost"
            value={`$${systemMetrics.totalCost}`}
            change={-5.1}
            icon={<Cloud />}
            color="#9c27b0"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={2}>
          <MetricCard
            title="Uptime"
            value={`${systemMetrics.uptime}%`}
            change={0.0}
            icon={<Security />}
            color="#f44336"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Agent Status */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              🤖 Agent Status
            </Typography>
            <Box sx={{ mt: 2 }}>
              {agentStatus.map((agent, index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1">{agent.icon}</Typography>
                      <Typography variant="body1">{agent.name}</Typography>
                    </Box>
                    <Chip
                      label={agent.status}
                      size="small"
                      sx={{
                        bgcolor: getStatusColor(agent.status),
                        color: 'white',
                        fontSize: '0.7rem',
                      }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="caption" color="textSecondary">
                      Load: {agent.load}%
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Requests: {agent.requests}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={agent.load}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: 'rgba(255,255,255,0.1)',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: getStatusColor(agent.status),
                      },
                    }}
                  />
                  {index < agentStatus.length - 1 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              📈 Performance Trends (24h)
            </Typography>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis 
                  dataKey="time" 
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                />
                <YAxis 
                  yAxisId="requests"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                />
                <YAxis 
                  yAxisId="responseTime"
                  orientation="right"
                  stroke="rgba(255,255,255,0.7)"
                  fontSize={12}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(30,30,30,0.95)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  yAxisId="requests"
                  type="monotone"
                  dataKey="requests"
                  stroke="#667eea"
                  strokeWidth={3}
                  dot={{ fill: '#667eea', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#667eea' }}
                />
                <Line
                  yAxisId="responseTime"
                  type="monotone"
                  dataKey="responseTime"
                  stroke="#764ba2"
                  strokeWidth={3}
                  dot={{ fill: '#764ba2', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#764ba2' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* LLM Usage */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '300px' }}>
            <Typography variant="h6" gutterBottom>
              🧠 LLM Usage Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={llmUsageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {llmUsageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '300px' }}>
            <Typography variant="h6" gutterBottom>
              📋 Recent Activity
            </Typography>
            <Box sx={{ mt: 2, maxHeight: '220px', overflow: 'auto' }}>
              {[
                { time: '2 phút trước', action: 'Athena tạo Jira ticket PROJ-123', status: 'success' },
                { time: '5 phút trước', action: 'Hephaestus deploy ứng dụng lên OpenShift', status: 'success' },
                { time: '8 phút trước', action: 'Apollo phân tích yêu cầu kinh doanh', status: 'success' },
                { time: '12 phút trước', action: 'LLM Pool chuyển từ GPT-4 sang Claude-3', status: 'info' },
                { time: '15 phút trước', action: 'Hermes cảnh báo doanh thu giảm', status: 'warning' },
                { time: '18 phút trước', action: 'Vulcan hoàn thành monitoring setup', status: 'success' },
              ].map((activity, index) => (
                <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    {activity.action}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {activity.time}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;