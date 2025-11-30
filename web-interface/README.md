# Zeus Nexus Web Interface

A modern React-based web interface for the Zeus Nexus Agentic AI Platform.

## Features

- **Interactive Dashboard**: Real-time monitoring of agents, tasks, and system metrics
- **Chat Interface**: Natural language interaction with Zeus Master Agent
- **Agent Management**: Monitor and control satellite agents (Athena, Apollo, Hephaestus)
- **LLM Pool Monitor**: Track usage, costs, and performance across multiple LLM providers
- **Task Tracker**: Visualize task execution flow, logs, and results
- **System Settings**: Comprehensive configuration management

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **UI Framework**: Material-UI v5 (MUI)
- **State Management**: Redux Toolkit
- **Charts**: Recharts for data visualization
- **Routing**: React Router v6
- **Build Tool**: Create React App with TypeScript template

## Architecture

```
web-interface/
├── public/
│   ├── index.html
│   └── manifest.json
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   └── Layout.tsx          # Main app layout with navigation
│   │   ├── Dashboard/
│   │   │   └── Dashboard.tsx       # System overview dashboard
│   │   ├── Chat/
│   │   │   └── ChatInterface.tsx   # Zeus interaction chat
│   │   ├── Agents/
│   │   │   └── AgentManager.tsx    # Agent monitoring & control
│   │   ├── LLM/
│   │   │   └── LLMMonitor.tsx      # LLM pool monitoring
│   │   ├── Tasks/
│   │   │   └── TaskTracker.tsx     # Task execution tracking
│   │   └── Settings/
│   │       └── SettingsPage.tsx    # System configuration
│   ├── store/
│   │   ├── index.ts                # Redux store configuration
│   │   └── slices/                 # Redux slices for state management
│   │       ├── agentSlice.ts
│   │       ├── chatSlice.ts
│   │       ├── llmSlice.ts
│   │       ├── taskSlice.ts
│   │       └── uiSlice.ts
│   ├── hooks/
│   │   └── redux.ts                # Typed Redux hooks
│   ├── theme.ts                    # Material-UI theme configuration
│   ├── App.tsx                     # Main app component
│   └── index.tsx                   # App entry point
├── package.json
└── tsconfig.json
```

## Installation & Setup

1. **Install Dependencies**
   ```bash
   cd web-interface
   npm install
   ```

2. **Development Mode**
   ```bash
   npm start
   ```
   Opens [http://localhost:3000](http://localhost:3000)

3. **Production Build**
   ```bash
   npm run build
   ```

4. **Run Tests**
   ```bash
   npm test
   ```

## Key Components

### Dashboard
- System metrics overview
- Agent status cards
- Performance charts
- Recent activity feeds

### Chat Interface
- Natural language interaction with Zeus
- Message history
- File uploads and attachments
- Real-time typing indicators

### Agent Manager
- Health monitoring for all satellite agents
- Load balancing controls
- Capability management
- Agent configuration dialogs

### LLM Monitor
- Multi-provider cost tracking
- Token usage analytics
- Response time monitoring
- Provider switching controls

### Task Tracker
- Real-time task execution visualization
- Execution logs and timeline
- Task control actions (pause, stop, retry)
- Progress tracking with detailed metadata

## State Management

The application uses Redux Toolkit for state management with the following slices:

- **agentSlice**: Agent status, health, and capabilities
- **chatSlice**: Chat messages and conversation state
- **llmSlice**: LLM provider metrics and configuration
- **taskSlice**: Task execution state and logs
- **uiSlice**: UI state (theme, notifications, modals)

## API Integration

The frontend integrates with Zeus Nexus backend services:

- **Zeus Master Agent**: `/api/orchestrator` - Main orchestration endpoint
- **Agent APIs**: `/api/agents/{agent-name}` - Individual agent endpoints
- **LLM Pool**: `/api/llm-pool` - LLM provider management
- **Task Management**: `/api/tasks` - Task execution and monitoring

## Theming

The application uses a custom Material-UI theme with:
- **Primary Color**: Blue gradient (#667eea to #764ba2)
- **Secondary Color**: Purple gradient (#f093fb to #f5576c)
- **Dark Mode**: Full dark theme support
- **Typography**: Roboto font family
- **Responsive Design**: Mobile-first approach

## Development Notes

- TypeScript compilation errors are expected until dependencies are installed
- Components are designed with Material-UI design principles
- State management follows Redux best practices
- All components are functional components with hooks
- Responsive design supports desktop, tablet, and mobile viewports

## Integration with Zeus Nexus

This web interface is designed to work seamlessly with the Zeus Nexus layered architecture:

1. **Layer 5 (Presentation)**: This React application
2. **Layer 4 (Zeus Master Agent)**: Orchestration and request routing
3. **Layer 3 (Satellite Agents)**: Specialized AI agents
4. **Layer 2 (ToolHub Services)**: External integrations
5. **Layer 1 (LLM Pool & Storage)**: Foundation services

## Future Enhancements

- Real-time WebSocket connections for live updates
- Advanced analytics and reporting
- Mobile app development
- Plugin system for custom components
- Multi-tenant support
- Advanced security features