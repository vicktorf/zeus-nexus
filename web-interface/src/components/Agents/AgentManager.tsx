import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { fetchAgents, toggleAgent, updateAgent } from '../../store/slices/agentSlice';

interface Agent {
  id: string;
  name: string;
  type: 'athena' | 'apollo' | 'hephaestus' | 'custom';
  status: 'active' | 'inactive' | 'busy' | 'error';
  health: number;
  load: number;
  capabilities: string[];
  lastActivity: string;
  version: string;
  endpoint: string;
}

export const AgentManager: React.FC = () => {
  const dispatch = useAppDispatch();
  const { agents, loading, error } = useAppSelector((state) => state.agents);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [configDialog, setConfigDialog] = useState(false);

  useEffect(() => {
    dispatch(fetchAgents());
  }, [dispatch]);

  const handleToggleAgent = (agentId: string) => {
    dispatch(toggleAgent(agentId));
  };

  const handleRefreshAgent = (agentId: string) => {
    // Implement agent refresh logic
    console.log('Refreshing agent:', agentId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'busy': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'athena': return '🧠';
      case 'apollo': return '🎯';
      case 'hephaestus': return '⚙️';
      default: return '🤖';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Agent Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setConfigDialog(true)}
        >
          Add Agent
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Agent Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {agents.map((agent) => (
          <Grid item xs={12} sm={6} lg={4} key={agent.id}>
            <Card 
              sx={{ 
                height: '100%',
                border: agent.status === 'active' ? 2 : 1,
                borderColor: agent.status === 'active' ? 'primary.main' : 'divider',
                cursor: 'pointer',
                '&:hover': { boxShadow: 6 }
              }}
              onClick={() => setSelectedAgent(agent)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h2" sx={{ mr: 1 }}>
                    {getTypeIcon(agent.type)}
                  </Typography>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="div">
                      {agent.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {agent.type.toUpperCase()}
                    </Typography>
                  </Box>
                  <Chip 
                    label={agent.status}
                    color={getStatusColor(agent.status) as any}
                    size="small"
                  />
                </Box>

                {/* Health & Load */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Health</Typography>
                    <Typography variant="body2">{agent.health}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={agent.health}
                    color={agent.health > 80 ? 'success' : agent.health > 50 ? 'warning' : 'error'}
                    sx={{ mb: 1 }}
                  />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Load</Typography>
                    <Typography variant="body2">{agent.load}%</Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={agent.load}
                    color={agent.load < 70 ? 'success' : agent.load < 90 ? 'warning' : 'error'}
                  />
                </Box>

                {/* Capabilities */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Capabilities ({agent.capabilities.length})
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {agent.capabilities.slice(0, 3).map((capability) => (
                      <Chip
                        key={capability}
                        label={capability}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                    {agent.capabilities.length > 3 && (
                      <Chip
                        label={`+${agent.capabilities.length - 3} more`}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    )}
                  </Box>
                </Box>

                {/* Actions */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Tooltip title={agent.status === 'active' ? 'Stop Agent' : 'Start Agent'}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleAgent(agent.id);
                        }}
                      >
                        {agent.status === 'active' ? <StopIcon /> : <PlayIcon />}
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Refresh">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRefreshAgent(agent.id);
                        }}
                      >
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    v{agent.version}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Detailed Agent Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Agent Details
          </Typography>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Agent</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Health</TableCell>
                  <TableCell>Load</TableCell>
                  <TableCell>Endpoint</TableCell>
                  <TableCell>Last Activity</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {agents.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography sx={{ mr: 1 }}>
                          {getTypeIcon(agent.type)}
                        </Typography>
                        {agent.name}
                      </Box>
                    </TableCell>
                    <TableCell>{agent.type.toUpperCase()}</TableCell>
                    <TableCell>
                      <Chip 
                        label={agent.status}
                        color={getStatusColor(agent.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {agent.health}%
                        {agent.health < 50 && <WarningIcon color="error" sx={{ ml: 1, fontSize: 16 }} />}
                      </Box>
                    </TableCell>
                    <TableCell>{agent.load}%</TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {agent.endpoint}
                      </Typography>
                    </TableCell>
                    <TableCell>{agent.lastActivity}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex' }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={agent.status === 'active'}
                              onChange={() => handleToggleAgent(agent.id)}
                              size="small"
                            />
                          }
                          label=""
                        />
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedAgent(agent);
                            setConfigDialog(true);
                          }}
                        >
                          <SettingsIcon />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Agent Configuration Dialog */}
      <Dialog
        open={configDialog}
        onClose={() => setConfigDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedAgent ? `Configure ${selectedAgent.name}` : 'Add New Agent'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Agent configuration interface will be implemented here.
            This includes capability settings, resource limits, and connection parameters.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};