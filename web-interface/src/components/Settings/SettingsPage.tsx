import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Tab,
  Tabs,
  Paper,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Tune as TuneIcon,
  Notifications as NotificationsIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
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

export const SettingsPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [settings, setSettings] = useState({
    // System Settings
    autoRefresh: true,
    refreshInterval: 30,
    darkMode: false,
    notifications: true,
    
    // Agent Settings
    maxConcurrentTasks: 5,
    taskTimeout: 300,
    retryAttempts: 3,
    
    // LLM Settings
    defaultProvider: 'openai',
    maxTokens: 4000,
    temperature: 0.7,
    costLimit: 100,
    
    // Security Settings
    sessionTimeout: 60,
    enableAuditLog: true,
    requireMFA: false,
    
    // Storage Settings
    logRetentionDays: 30,
    backupEnabled: true,
    backupInterval: 24,
  });

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = () => {
    console.log('Saving settings:', settings);
    // Implement settings save logic
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          System Settings
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            sx={{ mr: 2 }}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSaveSettings}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      {/* Success Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Changes will be applied after saving. Some settings may require a system restart.
      </Alert>

      {/* Settings Tabs */}
      <Paper elevation={1}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={(_, newValue) => setTabValue(newValue)}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="General" icon={<TuneIcon />} />
            <Tab label="Agents" icon={<SecurityIcon />} />
            <Tab label="LLM Pool" icon={<StorageIcon />} />
            <Tab label="Security" icon={<SecurityIcon />} />
            <Tab label="Storage" icon={<StorageIcon />} />
            <Tab label="Notifications" icon={<NotificationsIcon />} />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Interface Settings
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.autoRefresh}
                          onChange={(e) => handleSettingChange('autoRefresh', e.target.checked)}
                        />
                      }
                      label="Auto-refresh dashboard"
                    />
                    
                    <TextField
                      label="Refresh interval (seconds)"
                      type="number"
                      value={settings.refreshInterval}
                      onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                      disabled={!settings.autoRefresh}
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.darkMode}
                          onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
                        />
                      }
                      label="Dark mode"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notifications}
                          onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                        />
                      }
                      label="Enable notifications"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Performance Settings
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Max concurrent dashboard updates"
                      type="number"
                      defaultValue={10}
                    />
                    
                    <TextField
                      label="Chart data points limit"
                      type="number"
                      defaultValue={100}
                    />
                    
                    <FormControl fullWidth>
                      <InputLabel>Default time range</InputLabel>
                      <Select defaultValue="24h" label="Default time range">
                        <MenuItem value="1h">1 Hour</MenuItem>
                        <MenuItem value="6h">6 Hours</MenuItem>
                        <MenuItem value="24h">24 Hours</MenuItem>
                        <MenuItem value="7d">7 Days</MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Agent Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Agent Execution Settings
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Max concurrent tasks per agent"
                      type="number"
                      value={settings.maxConcurrentTasks}
                      onChange={(e) => handleSettingChange('maxConcurrentTasks', parseInt(e.target.value))}
                    />
                    
                    <TextField
                      label="Task timeout (seconds)"
                      type="number"
                      value={settings.taskTimeout}
                      onChange={(e) => handleSettingChange('taskTimeout', parseInt(e.target.value))}
                    />
                    
                    <TextField
                      label="Retry attempts on failure"
                      type="number"
                      value={settings.retryAttempts}
                      onChange={(e) => handleSettingChange('retryAttempts', parseInt(e.target.value))}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Agent Health Monitoring
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Health check interval (seconds)"
                      type="number"
                      defaultValue={30}
                    />
                    
                    <TextField
                      label="Unhealthy threshold (%)"
                      type="number"
                      defaultValue={50}
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Auto-restart unhealthy agents"
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Load balancing enabled"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* LLM Pool Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    LLM Configuration
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <FormControl fullWidth>
                      <InputLabel>Default LLM Provider</InputLabel>
                      <Select
                        value={settings.defaultProvider}
                        label="Default LLM Provider"
                        onChange={(e) => handleSettingChange('defaultProvider', e.target.value)}
                      >
                        <MenuItem value="openai">OpenAI GPT-4</MenuItem>
                        <MenuItem value="anthropic">Anthropic Claude 3</MenuItem>
                        <MenuItem value="local">Local Llama 2</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <TextField
                      label="Max tokens per request"
                      type="number"
                      value={settings.maxTokens}
                      onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
                    />
                    
                    <TextField
                      label="Temperature (0.0 - 2.0)"
                      type="number"
                      step="0.1"
                      value={settings.temperature}
                      onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
                      inputProps={{ min: 0, max: 2, step: 0.1 }}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Cost Management
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Daily cost limit ($)"
                      type="number"
                      value={settings.costLimit}
                      onChange={(e) => handleSettingChange('costLimit', parseFloat(e.target.value))}
                    />
                    
                    <TextField
                      label="Cost alert threshold (%)"
                      type="number"
                      defaultValue={80}
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Auto-fallback to cheaper models"
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Enable cost tracking"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Access Control
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Session timeout (minutes)"
                      type="number"
                      value={settings.sessionTimeout}
                      onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.requireMFA}
                          onChange={(e) => handleSettingChange('requireMFA', e.target.checked)}
                        />
                      }
                      label="Require multi-factor authentication"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.enableAuditLog}
                          onChange={(e) => handleSettingChange('enableAuditLog', e.target.checked)}
                        />
                      }
                      label="Enable audit logging"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    API Security
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="API rate limit (requests/minute)"
                      type="number"
                      defaultValue={100}
                    />
                    
                    <TextField
                      label="Max API key age (days)"
                      type="number"
                      defaultValue={90}
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Require API key rotation"
                    />
                    
                    <Button variant="outlined" fullWidth>
                      Generate New API Key
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Storage Settings */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Data Retention
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Log retention period (days)"
                      type="number"
                      value={settings.logRetentionDays}
                      onChange={(e) => handleSettingChange('logRetentionDays', parseInt(e.target.value))}
                    />
                    
                    <TextField
                      label="Task history retention (days)"
                      type="number"
                      defaultValue={90}
                    />
                    
                    <TextField
                      label="Chat history retention (days)"
                      type="number"
                      defaultValue={365}
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Backup Settings
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.backupEnabled}
                          onChange={(e) => handleSettingChange('backupEnabled', e.target.checked)}
                        />
                      }
                      label="Enable automatic backups"
                    />
                    
                    <TextField
                      label="Backup interval (hours)"
                      type="number"
                      value={settings.backupInterval}
                      onChange={(e) => handleSettingChange('backupInterval', parseInt(e.target.value))}
                      disabled={!settings.backupEnabled}
                    />
                    
                    <Button variant="outlined" fullWidth>
                      Create Backup Now
                    </Button>
                    
                    <Button variant="outlined" fullWidth>
                      Restore from Backup
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notifications Settings */}
        <TabPanel value={tabValue} index={5}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Notification Preferences
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Task completion notifications"
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Agent error notifications"
                    />
                    
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Cost threshold alerts"
                    />
                    
                    <FormControlLabel
                      control={<Switch />}
                      label="System maintenance notifications"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 3 }}>
                    Notification Channels
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <TextField
                      label="Email address"
                      type="email"
                      defaultValue="admin@example.com"
                      fullWidth
                    />
                    
                    <TextField
                      label="Slack webhook URL"
                      placeholder="https://hooks.slack.com/..."
                      fullWidth
                    />
                    
                    <Button variant="outlined" fullWidth>
                      Test Notifications
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};