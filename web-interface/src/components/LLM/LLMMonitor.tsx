import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  AccountBalance as BalanceIcon,
  SwapHoriz as SwapIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';

interface LLMProvider {
  id: string;
  name: string;
  type: 'openai' | 'anthropic' | 'local';
  status: 'active' | 'inactive' | 'error';
  endpoint: string;
  model: string;
  tokensUsed: number;
  cost: number;
  responseTime: number;
  requests: number;
  errorRate: number;
}

interface UsageMetric {
  timestamp: string;
  provider: string;
  tokens: number;
  cost: number;
  responseTime: number;
}

const mockProviders: LLMProvider[] = [
  {
    id: 'openai-gpt4',
    name: 'OpenAI GPT-4',
    type: 'openai',
    status: 'active',
    endpoint: 'api.openai.com',
    model: 'gpt-4-turbo-preview',
    tokensUsed: 125000,
    cost: 15.25,
    responseTime: 2.3,
    requests: 245,
    errorRate: 0.8,
  },
  {
    id: 'anthropic-claude',
    name: 'Anthropic Claude 3',
    type: 'anthropic',
    status: 'active',
    endpoint: 'api.anthropic.com',
    model: 'claude-3-opus-20240229',
    tokensUsed: 89000,
    cost: 8.90,
    responseTime: 1.9,
    requests: 156,
    errorRate: 0.3,
  },
  {
    id: 'local-llama',
    name: 'Local Llama 2',
    type: 'local',
    status: 'active',
    endpoint: 'localhost:11434',
    model: 'llama2:13b',
    tokensUsed: 67000,
    cost: 0.0,
    responseTime: 3.2,
    requests: 98,
    errorRate: 2.1,
  },
];

const mockUsageData: UsageMetric[] = [
  { timestamp: '00:00', provider: 'OpenAI', tokens: 1200, cost: 0.12, responseTime: 2.1 },
  { timestamp: '04:00', provider: 'OpenAI', tokens: 890, cost: 0.089, responseTime: 2.3 },
  { timestamp: '08:00', provider: 'Anthropic', tokens: 1450, cost: 0.145, responseTime: 1.8 },
  { timestamp: '12:00', provider: 'Local', tokens: 2100, cost: 0.0, responseTime: 3.5 },
  { timestamp: '16:00', provider: 'OpenAI', tokens: 1680, cost: 0.168, responseTime: 2.0 },
  { timestamp: '20:00', provider: 'Anthropic', tokens: 1320, cost: 0.132, responseTime: 1.9 },
];

export const LLMMonitor: React.FC = () => {
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  const [configDialog, setConfigDialog] = useState(false);
  const [providers] = useState<LLMProvider[]>(mockProviders);

  const totalCost = providers.reduce((sum, provider) => sum + provider.cost, 0);
  const totalTokens = providers.reduce((sum, provider) => sum + provider.tokensUsed, 0);
  const totalRequests = providers.reduce((sum, provider) => sum + provider.requests, 0);
  const avgResponseTime = providers.reduce((sum, provider) => sum + provider.responseTime, 0) / providers.length;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'openai': return '🤖';
      case 'anthropic': return '🧠';
      case 'local': return '💻';
      default: return '🔮';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          LLM Pool Monitor
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<SettingsIcon />}
            onClick={() => setConfigDialog(true)}
          >
            Configure
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <BalanceIcon color="primary" sx={{ mr: 2, fontSize: 32 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Cost (24h)
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    ${totalCost.toFixed(2)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUpIcon color="success" sx={{ mr: 2, fontSize: 32 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Tokens Used
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {(totalTokens / 1000).toFixed(1)}K
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SwapIcon color="info" sx={{ mr: 2, fontSize: 32 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Requests
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {totalRequests}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <SpeedIcon color="warning" sx={{ mr: 2, fontSize: 32 }} />
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Avg Response Time
                  </Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {avgResponseTime.toFixed(1)}s
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Provider Status Table */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Provider Status
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Provider</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Model</TableCell>
                      <TableCell align="right">Tokens</TableCell>
                      <TableCell align="right">Cost</TableCell>
                      <TableCell align="right">Response Time</TableCell>
                      <TableCell align="right">Error Rate</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {providers.map((provider) => (
                      <TableRow key={provider.id}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography sx={{ mr: 1 }}>
                              {getProviderIcon(provider.type)}
                            </Typography>
                            {provider.name}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={provider.status}
                            color={getStatusColor(provider.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {provider.model}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          {(provider.tokensUsed / 1000).toFixed(1)}K
                        </TableCell>
                        <TableCell align="right">
                          ${provider.cost.toFixed(2)}
                        </TableCell>
                        <TableCell align="right">
                          {provider.responseTime.toFixed(1)}s
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            color={provider.errorRate > 2 ? 'error' : provider.errorRate > 1 ? 'warning' : 'success'}
                          >
                            {provider.errorRate.toFixed(1)}%
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Usage Chart */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Usage Trends (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockUsageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="tokens" stroke="#2196f3" strokeWidth={2} />
                  <Line type="monotone" dataKey="cost" stroke="#ff9800" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          {/* Cost Breakdown */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Cost Breakdown
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={providers}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="cost" fill="#4caf50" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Provider Health */}
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Provider Health
              </Typography>
              {providers.map((provider) => (
                <Box key={provider.id} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">
                      {getProviderIcon(provider.type)} {provider.name}
                    </Typography>
                    <Typography variant="body2">
                      {100 - provider.errorRate}% healthy
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={100 - provider.errorRate}
                    color={provider.errorRate < 1 ? 'success' : provider.errorRate < 3 ? 'warning' : 'error'}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Configuration Dialog */}
      <Dialog
        open={configDialog}
        onClose={() => setConfigDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>LLM Pool Configuration</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Primary Provider</InputLabel>
              <Select
                value="openai-gpt4"
                label="Primary Provider"
              >
                {providers.map((provider) => (
                  <MenuItem key={provider.id} value={provider.id}>
                    {getProviderIcon(provider.type)} {provider.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Cost Limit ($/day)"
              type="number"
              defaultValue={100}
            />

            <TextField
              fullWidth
              label="Token Limit (K/hour)"
              type="number"
              defaultValue={50}
            />

            <Alert severity="info">
              Load balancing and failover rules can be configured here.
              The system will automatically switch providers based on cost, performance, and availability.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button variant="contained">Save Configuration</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};