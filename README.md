# AI Assistant CLI

A web-based terminal interface for interacting with AI assistants, featuring real-time streaming responses, knowledge base integration, and custom agent support.

## 🚀 Features

- **Terminal-like Interface**: Familiar command-line experience in a web browser using xterm.js
- **Real-time AI Interactions**: Streaming responses from AWS Bedrock Nova Pro model
- **Knowledge Base Integration**: RAG (Retrieval Augmented Generation) capabilities with AWS Bedrock Knowledge Bases
- **Custom Agent Integration**: Birmingham weather/time agent for location-specific data
- **Session Management**: Persistent conversation history with DynamoDB storage
- **Authentication**: Enterprise-grade AWS Identity Center (SSO) integration
- **WebSocket Communication**: Real-time bidirectional communication
- **Responsive Design**: Works on desktop and mobile devices
- **Error Handling**: Comprehensive error handling with circuit breakers
- **Monitoring**: CloudWatch integration for logs and metrics

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Development](#development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Prerequisites

- WSL Ubuntu (for Windows development)
- Python 3.12+
- Node.js 18+ and npm
- AWS CLI configured with appropriate permissions
- Terraform (for infrastructure deployment)

### Development Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/ai-assistant-cli
   ```

2. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   pip install -r agent/requirements.txt
   ```

4. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Environment Configuration**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your AWS configuration
   
   # Frontend
   cp frontend/.env.example frontend/.env.local
   # Edit frontend/.env.local with your configuration
   ```

6. **AWS Services Setup**
   - Enable AWS Bedrock Nova Pro model access
   - Create DynamoDB table for sessions
   - Set up AWS Identity Center application
   - Configure Knowledge Bases (optional)

7. **Run the Application**
   ```bash
   # Terminal 1: Backend
   source venv/bin/activate
   cd backend
   python main.py
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   
   # Terminal 3: Agent (optional)
   source venv/bin/activate
   python agent/birmingham_agent.py
   ```

8. **Access the Application**
   Open http://localhost:5173 in your browser

## 🏗️ Architecture

### System Overview

The AI Assistant CLI is built on a modern, scalable architecture leveraging AWS services:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Frontend  │    │   Backend    │    │  AWS Services   │
│             │    │              │    │                 │
│ React + TS  │◄──►│ FastAPI      │◄──►│ Bedrock Nova    │
│ xterm.js    │    │ WebSockets   │    │ Knowledge Bases │
│ WebSocket   │    │ Integration  │    │ Identity Center │
│             │    │ Service      │    │ DynamoDB        │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Key Components

- **Frontend**: React TypeScript application with terminal interface
- **Backend**: FastAPI application with WebSocket support and service orchestration
- **Integration Service**: Orchestrates all backend services and handles request routing
- **AI Services**: AWS Bedrock Nova Pro for general AI queries
- **Knowledge Base**: AWS Bedrock Knowledge Bases for RAG capabilities
- **Agent Service**: Custom Birmingham agent for weather/time data
- **Authentication**: AWS Identity Center (SSO) with JWT token validation
- **Storage**: DynamoDB for session management, S3 for knowledge base documents

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 💻 Development

### Project Structure

```
ai-assistant-cli/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Application entry point
│   ├── config.py           # Configuration management
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic services
│   ├── models/             # Data models
│   ├── middleware/         # Custom middleware
│   └── tests/              # Backend tests
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API and WebSocket services
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Utility functions
│   └── tests/              # Frontend tests
├── terraform/              # Infrastructure as Code
├── docs/                   # Documentation
├── agent/                  # Birmingham agent implementation
├── .kiro/                  # Kiro specifications and configuration
└── venv/                   # Python virtual environment
```

### Key Services

#### Backend Services
- **Integration Service**: Orchestrates all backend services and handles command routing
- **Auth Service**: JWT token validation and user context management
- **Session Service**: DynamoDB-based session and conversation management
- **Bedrock Service**: AWS Bedrock Nova Pro integration with streaming support
- **Knowledge Base Service**: RAG queries using Bedrock Knowledge Bases
- **Agent Service**: Custom agent integration (Birmingham weather/time)

#### Frontend Services
- **WebSocket Service**: Real-time communication with backend
- **Knowledge Base Service**: API integration for knowledge base management
- **Session Service**: Session management and persistence
- **Command Processor**: Built-in command handling (help, clear, etc.)

### Development Commands

```bash
# Backend
source venv/bin/activate
cd backend
python -m pytest                    # Run tests
python -m pytest --cov             # Run tests with coverage
python main.py                     # Start development server

# Frontend
cd frontend
npm run dev                         # Start development server
npm run build                       # Build for production
npm run test                        # Run tests
npm run test:watch                  # Run tests in watch mode
npm run lint                        # Run ESLint

# Agent
source venv/bin/activate
python agent/birmingham_agent.py   # Start agent service
```

## 🚀 Deployment

The application is designed for deployment on AWS using modern cloud-native practices.

### Deployment Architecture

- **Frontend**: S3 + CloudFront for global CDN
- **Backend**: ECS Fargate with Application Load Balancer
- **Database**: DynamoDB with auto-scaling
- **Authentication**: AWS Identity Center integration
- **Monitoring**: CloudWatch Logs and Metrics
- **Infrastructure**: Terraform for Infrastructure as Code

### Quick Deployment

```bash
# 1. Deploy infrastructure
cd terraform
terraform init
terraform plan
terraform apply

# 2. Build and deploy backend
cd backend
docker build -t ai-assistant-cli-backend .
# Push to ECR and update ECS service

# 3. Build and deploy frontend
cd frontend
npm run build
aws s3 sync dist/ s3://your-frontend-bucket/
aws cloudfront create-invalidation --distribution-id YOUR-ID --paths "/*"
```

For comprehensive deployment instructions, see [DEPLOYMENT.md](docs/DEPLOYMENT.md).

## 📚 API Documentation

### WebSocket API

The application uses WebSocket for real-time communication:

#### Message Types

```typescript
interface WebSocketMessage {
  type: 'command' | 'response' | 'error' | 'status' | 'agent_response' | 'knowledge_base_switch';
  content: string;
  sessionId: string;
  knowledgeBaseId?: string;
  timestamp: string;
  streaming?: boolean;
  metadata?: Record<string, any>;
}
```

#### Command Examples

```javascript
// Send AI query
{
  "type": "command",
  "content": "Tell me about machine learning",
  "sessionId": "session-123",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Agent command
{
  "type": "command",
  "content": "what time is it",
  "sessionId": "session-123",
  "timestamp": "2024-01-01T00:00:00Z"
}

// Knowledge base query
{
  "type": "command",
  "content": "kb: search for documentation",
  "sessionId": "session-123",
  "knowledgeBaseId": "kb-123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### REST API

The backend also provides REST endpoints:

- `GET /api/v1/health` - Health check
- `GET /api/v1/sessions` - List user sessions
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/knowledge-bases` - List knowledge bases
- `GET /api/v1/agent/status` - Agent status

## 🧪 Testing

### Backend Testing

```bash
source venv/bin/activate
cd backend
python -m pytest                           # Run all tests
python -m pytest tests/test_integration_flow.py  # Integration tests
python -m pytest --cov                     # Coverage report
python -m pytest -v                        # Verbose output
```

### Frontend Testing

```bash
cd frontend
npm test                                    # Run all tests
npm run test:watch                          # Watch mode
npm test -- --coverage                     # Coverage report
npm test integration.test.tsx              # Specific test file
```

### End-to-End Testing

```bash
# Test backend integration directly
python test_agent_direct.py

# Test complete system
python test_integration_simple.py
```

### Test Categories

- **Unit Tests**: Individual component/service testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete user workflow testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization testing

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Process

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**
   ```bash
   # Backend
   source venv/bin/activate
   cd backend && python -m pytest
   
   # Frontend
   cd frontend && npm test
   ```
5. **Submit a pull request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI passes

### Development Workflow

This project follows a spec-driven development approach:

1. **Requirements**: Defined in `.kiro/specs/ai-assistant-cli/requirements.md`
2. **Design**: Documented in `.kiro/specs/ai-assistant-cli/design.md`
3. **Implementation**: Task-based approach in `.kiro/specs/ai-assistant-cli/tasks.md`

### Code Style

- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Follow TypeScript best practices, use Prettier
- **Commits**: Use conventional commit messages
- **Documentation**: Update relevant documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md) - Detailed system architecture
- [Deployment Guide](docs/DEPLOYMENT.md) - Comprehensive deployment instructions
- [Kiro Specifications](.kiro/specs/ai-assistant-cli/) - Requirements, design, and tasks

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check existing documentation
- Review the troubleshooting section in the deployment guide

---

**Built with ❤️ using AWS, React, and Python**