# ⚡ Zeus Nexus Frontend

Streamlit-based web interface for Zeus Nexus AI Pantheon.

## 🚀 Features

- 💬 **Chat Interface** - Real-time chat with Zeus AI agents
- 🤖 **LLM Selector** - Choose from multiple LLM models (GPT-4, Claude, Gemini)
- 🎭 **Agent Discovery** - Browse and interact with 7 AI agents
- 🏥 **Health Monitoring** - Real-time system health checks
- 📊 **Response Metadata** - Detailed agent routing and capabilities info
- 🎨 **Modern UI** - Beautiful gradient design with responsive layout

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Access to Zeus Core API

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## 🐳 Docker Build

```bash
# Build image
docker build -t zeus-frontend:latest .

# Run container
docker run -p 8501:8501 zeus-frontend:latest
```

## ☸️ OpenShift Deployment

### Build on OpenShift

```bash
# Create build config
oc new-build --name=zeus-frontend --binary --strategy=docker -n ac-agentic

# Start build from local directory
oc start-build zeus-frontend --from-dir=. --follow -n ac-agentic
```

### Deploy

```bash
# Apply deployment manifest
oc apply -f deployment.yaml

# Check status
oc get pods -n ac-agentic | grep zeus-frontend

# Get route
oc get route zeus-frontend -n ac-agentic
```

### Access

Frontend URL: `https://zeus-ui-ac-agentic.apps.prod01.fis-cloud.fpt.com`

## 🎯 Usage

1. **Select LLM Model** - Choose your preferred AI model from the sidebar
2. **Check Health** - Verify Zeus Core is running
3. **Load Agents** - Discover available AI agents
4. **Start Chatting** - Type your message and let Zeus route to the right agent

### Example Queries

- **Project Management** (Athena): "Show me current Jira projects"
- **DevOps Monitoring** (Ares): "Check Grafana alerts"
- **Sales Analytics** (Apollo): "Show revenue for this month"
- **Cloud Infrastructure** (Hephaestus): "Deploy using Terraform"
- **CRM Operations** (Hermes): "Update customer in Notion"
- **Documentation** (Clio): "Generate project report"
- **Knowledge Learning** (Mnemosyne): "Learn from recent tickets"

## 📦 Dependencies

- `streamlit==1.29.0` - Web framework
- `requests==2.31.0` - HTTP client
- `streamlit-chat==0.1.1` - Chat UI components
- `python-dotenv==1.0.0` - Environment config

## 🔧 Configuration

Environment variables (optional):

```bash
ZEUS_API_URL=https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com
```

## 🎨 Features Highlight

### Chat Interface
- Real-time message streaming
- Session management
- Message history
- Agent routing visualization

### LLM Models Supported
- GPT-4 / GPT-4 Turbo / GPT-3.5 Turbo
- Claude 3 (Opus / Sonnet / Haiku)
- Gemini Pro / Gemini 1.5 Pro

### System Health
- Zeus Core API status
- Redis connection
- PostgreSQL connection
- Real-time health checks

## 📝 Notes

- Default port: `8501`
- Non-root user (UID 1001) for OpenShift compatibility
- Health check endpoint: `/_stcore/health`
- Session state persists during browser session

## 🐛 Troubleshooting

### Cannot connect to Zeus Core
```bash
# Check Zeus Core is running
oc get pods -n ac-agentic | grep zeus-core

# Check route
oc get route zeus-core -n ac-agentic

# Test API directly
curl https://zeus-ac-agentic.apps.prod01.fis-cloud.fpt.com/health
```

### Frontend pods not starting
```bash
# Check pod logs
oc logs -f deployment/zeus-frontend -n ac-agentic

# Check events
oc get events -n ac-agentic --sort-by='.lastTimestamp'
```

## 🚀 Roadmap

- [ ] WebSocket support for real-time streaming
- [ ] Chat history persistence
- [ ] Multi-user authentication
- [ ] Advanced analytics dashboard
- [ ] Voice input/output
- [ ] File upload for context
