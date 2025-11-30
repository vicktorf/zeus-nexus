import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tabs,
  Tab,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';

interface Task {
  id: string;
  title: string;
  description: string;
  type: 'agent_request' | 'llm_generation' | 'tool_execution' | 'workflow';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assignedAgent: string;
  createdAt: string;
  updatedAt: string;
  progress: number;
  duration?: string;
  logs: TaskLog[];
  metadata: Record<string, any>;
}

interface TaskLog {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  component?: string;
}

const mockTasks: Task[] = [
  {
    id: 'task-001',
    title: 'Generate OpenShift Deployment Manifests',
    description: 'Create Kubernetes deployment manifests for microservices architecture',
    type: 'agent_request',
    status: 'running',
    priority: 'high',
    assignedAgent: 'Hephaestus',
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-15T10:45:00Z',
    progress: 65,
    logs: [
      { timestamp: '10:30:00', level: 'info', message: 'Task initiated by user', component: 'Orchestrator' },
      { timestamp: '10:32:00', level: 'info', message: 'Analyzing requirements', component: 'Hephaestus' },
      { timestamp: '10:35:00', level: 'info', message: 'Generating deployment templates', component: 'Hephaestus' },
      { timestamp: '10:40:00', level: 'warning', message: 'Resource limits not specified, using defaults', component: 'Hephaestus' },
      { timestamp: '10:45:00', level: 'info', message: 'Generated 5/8 manifest files', component: 'Hephaestus' },
    ],
    metadata: { manifests_generated: 5, total_manifests: 8 },
  },
  {
    id: 'task-002',
    title: 'Project Management Analysis',
    description: 'Analyze sprint progress and generate recommendations',
    type: 'llm_generation',
    status: 'completed',
    priority: 'medium',
    assignedAgent: 'Athena',
    createdAt: '2024-01-15T09:15:00Z',
    updatedAt: '2024-01-15T09:45:00Z',
    progress: 100,
    duration: '30m',
    logs: [
      { timestamp: '09:15:00', level: 'info', message: 'Fetching JIRA data', component: 'Athena' },
      { timestamp: '09:20:00', level: 'info', message: 'Processing sprint metrics', component: 'LLM-Pool' },
      { timestamp: '09:35:00', level: 'info', message: 'Generating analysis report', component: 'LLM-Pool' },
      { timestamp: '09:45:00', level: 'info', message: 'Task completed successfully', component: 'Athena' },
    ],
    metadata: { tickets_analyzed: 25, recommendations: 8 },
  },
  {
    id: 'task-003',
    title: 'Cloud Cost Optimization',
    description: 'Identify opportunities for reducing cloud infrastructure costs',
    type: 'workflow',
    status: 'failed',
    priority: 'medium',
    assignedAgent: 'Apollo',
    createdAt: '2024-01-15T08:00:00Z',
    updatedAt: '2024-01-15T08:30:00Z',
    progress: 25,
    duration: '30m',
    logs: [
      { timestamp: '08:00:00', level: 'info', message: 'Connecting to cloud provider APIs', component: 'Apollo' },
      { timestamp: '08:10:00', level: 'warning', message: 'Rate limit encountered for AWS API', component: 'Apollo' },
      { timestamp: '08:25:00', level: 'error', message: 'Authentication failed for Azure API', component: 'Apollo' },
      { timestamp: '08:30:00', level: 'error', message: 'Task failed due to API access issues', component: 'Apollo' },
    ],
    metadata: { apis_checked: 2, errors: 3 },
  },
];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`task-tabpanel-${index}`}
      aria-labelledby={`task-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export const TaskTracker: React.FC = () => {
  const [tasks] = useState<Task[]>(mockTasks);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailDialog, setDetailDialog] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'error';
      case 'paused': return 'default';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckIcon color="success" />;
      case 'running': return <PlayIcon color="info" />;
      case 'pending': return <ScheduleIcon color="warning" />;
      case 'failed': return <ErrorIcon color="error" />;
      case 'paused': return <PauseIcon color="action" />;
      default: return <ScheduleIcon />;
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      case 'debug': return 'default';
      default: return 'default';
    }
  };

  const handleTaskAction = (taskId: string, action: string) => {
    console.log(`${action} task:`, taskId);
    // Implement task control logic
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          Task Execution Tracker
        </Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
        >
          Refresh
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="info.main">
                Running Tasks
              </Typography>
              <Typography variant="h3" fontWeight="bold">
                {tasks.filter(task => task.status === 'running').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="warning.main">
                Pending Tasks
              </Typography>
              <Typography variant="h3" fontWeight="bold">
                {tasks.filter(task => task.status === 'pending').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="success.main">
                Completed Today
              </Typography>
              <Typography variant="h3" fontWeight="bold">
                {tasks.filter(task => task.status === 'completed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="error.main">
                Failed Tasks
              </Typography>
              <Typography variant="h3" fontWeight="bold">
                {tasks.filter(task => task.status === 'failed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Active Tasks" />
          <Tab label="Task History" />
          <Tab label="Execution Logs" />
        </Tabs>
      </Box>

      {/* Active Tasks */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          {tasks.filter(task => ['running', 'pending', 'paused'].includes(task.status)).map((task) => (
            <Grid item xs={12} lg={6} key={task.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        {getStatusIcon(task.status)}
                        <Typography variant="h6" sx={{ ml: 1 }}>
                          {task.title}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {task.description}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                        <Chip
                          label={task.status}
                          color={getStatusColor(task.status) as any}
                          size="small"
                        />
                        <Chip
                          label={task.priority}
                          color={getPriorityColor(task.priority) as any}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={task.assignedAgent}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                  </Box>

                  {/* Progress */}
                  {task.status === 'running' && (
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">Progress</Typography>
                        <Typography variant="body2">{task.progress}%</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={task.progress} />
                    </Box>
                  )}

                  {/* Actions */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Box>
                      {task.status === 'running' && (
                        <IconButton
                          size="small"
                          onClick={() => handleTaskAction(task.id, 'pause')}
                        >
                          <PauseIcon />
                        </IconButton>
                      )}
                      {task.status === 'paused' && (
                        <IconButton
                          size="small"
                          onClick={() => handleTaskAction(task.id, 'resume')}
                        >
                          <PlayIcon />
                        </IconButton>
                      )}
                      <IconButton
                        size="small"
                        onClick={() => handleTaskAction(task.id, 'stop')}
                      >
                        <StopIcon />
                      </IconButton>
                    </Box>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => {
                        setSelectedTask(task);
                        setDetailDialog(true);
                      }}
                    >
                      Details
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Task History */}
      <TabPanel value={tabValue} index={1}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Task</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Priority</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {task.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {task.type.replace('_', ' ').toUpperCase()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{task.assignedAgent}</TableCell>
                  <TableCell>
                    <Chip
                      label={task.status}
                      color={getStatusColor(task.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={task.priority}
                      color={getPriorityColor(task.priority) as any}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>{task.duration || '-'}</TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(task.createdAt).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedTask(task);
                        setDetailDialog(true);
                      }}
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Execution Logs */}
      <TabPanel value={tabValue} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Recent Execution Logs
            </Typography>
            <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
              {tasks.flatMap(task => 
                task.logs.map(log => ({
                  ...log,
                  taskId: task.id,
                  taskTitle: task.title
                }))
              ).sort((a, b) => b.timestamp.localeCompare(a.timestamp)).map((log, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Chip
                        label={log.level}
                        color={getLogLevelColor(log.level) as any}
                        size="small"
                        sx={{ mr: 2 }}
                      />
                      <Typography variant="body2" sx={{ mr: 2 }}>
                        {log.timestamp}
                      </Typography>
                      <Typography variant="body2" sx={{ flexGrow: 1 }}>
                        {log.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {log.component}
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      <Typography variant="body2">
                        <strong>Task:</strong> {(log as any).taskTitle}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Component:</strong> {log.component}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Timestamp:</strong> {log.timestamp}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Message:</strong> {log.message}
                      </Typography>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Task Detail Dialog */}
      <Dialog
        open={detailDialog}
        onClose={() => setDetailDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Task Details: {selectedTask?.title}
        </DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ mb: 2 }}>Task Information</Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Status</Typography>
                    <Chip
                      label={selectedTask.status}
                      color={getStatusColor(selectedTask.status) as any}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Priority</Typography>
                    <Chip
                      label={selectedTask.priority}
                      color={getPriorityColor(selectedTask.priority) as any}
                    />
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Assigned Agent</Typography>
                    <Typography>{selectedTask.assignedAgent}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Progress</Typography>
                    <LinearProgress variant="determinate" value={selectedTask.progress} />
                    <Typography variant="body2">{selectedTask.progress}%</Typography>
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" sx={{ mb: 2 }}>Execution Timeline</Typography>
                <Timeline>
                  {selectedTask.logs.map((log, index) => (
                    <TimelineItem key={index}>
                      <TimelineSeparator>
                        <TimelineDot color={getLogLevelColor(log.level) as any} />
                        {index < selectedTask.logs.length - 1 && <TimelineConnector />}
                      </TimelineSeparator>
                      <TimelineContent>
                        <Typography variant="body2" fontWeight="medium">
                          {log.message}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {log.timestamp} - {log.component}
                        </Typography>
                      </TimelineContent>
                    </TimelineItem>
                  ))}
                </Timeline>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialog(false)}>Close</Button>
          <Button variant="contained" startIcon={<DownloadIcon />}>
            Export Logs
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};