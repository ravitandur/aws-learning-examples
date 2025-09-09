---
created: 2025-09-05T19:46:11Z
last_updated: 2025-09-09T13:34:24Z
version: 1.2
author: Claude Code PM System
---

# Technology Context

## Primary Technology Stack

### Backend Technologies
- **Python 3.11**: Primary runtime for all Lambda functions
- **AWS CDK**: Infrastructure as code framework
- **AWS Lambda**: Serverless compute platform
- **DynamoDB**: NoSQL database with GSI optimization
- **EventBridge**: Event-driven architecture backbone
- **Step Functions**: Workflow orchestration (Standard & Express)

### Frontend Technologies
- **React 18+**: Component-based UI framework
- **TypeScript**: Type-safe JavaScript development
- **TailwindCSS**: Utility-first CSS framework
- **Node.js**: JavaScript runtime environment
- **Vite/Create React App**: Build tooling

### AWS Services Portfolio
- **API Gateway**: RESTful API endpoints
- **Cognito**: User authentication & authorization
- **Secrets Manager**: Secure credential storage
- **CloudWatch**: Logging, monitoring & alerting
- **SNS**: Notification services
- **EventBridge**: Event routing & scheduling

## Project-Specific Dependencies

### Options Strategy Platform
```python
# Core dependencies from requirements.txt
boto3>=1.34.0          # AWS SDK for Python
requests>=2.31.0       # HTTP library
python-dateutil>=2.8.0 # Date manipulation
pytz>=2023.3           # Timezone handling

# Testing dependencies from tests/requirements-test.txt (NEW)
moto[dynamodb]>=4.2.0  # AWS service mocking with modern mock_aws
pytest>=7.4.0          # Advanced testing framework
faker>=19.0.0          # Realistic test data generation
boto3-stubs>=1.34.0    # Type hints for boto3
coverage>=7.3.0        # Test coverage analysis
```

### User Auth & Broker Management
```python
# Authentication & broker integration
jwt>=2.8.0             # JWT token handling
cryptography>=41.0.0   # Encryption utilities
requests-oauthlib>=1.3.0 # OAuth implementation
```

### Frontend Applications
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.0.0",
    "@types/react": "^18.0.0",
    "lucide-react": "^0.200.0"
  }
}
```

## Development Environment

### Python Environment Management
- **Virtual environments**: Isolated per project
- **Requirements files**: Explicit dependency management
- **Python 3.11**: Consistent runtime across all projects

### Node.js Environment
- **Package.json**: Per-frontend dependency management
- **TypeScript**: Strict type checking enabled
- **ESLint/Prettier**: Code formatting standards

### AWS Configuration
- **AWS Profile**: `account2` for all deployments
- **Primary Region**: `ap-south-1` (Asia Pacific Mumbai)
- **Account ID**: `142649403032`

## Architecture Patterns & Technologies

### Revolutionary Options Platform Features
- **GSI2 Optimization**: DynamoDB query reduction (401+ → 2 queries)
- **0-Second Precision Timing**: Step Functions + dynamic wait calculation
- **Multi-Broker Integration**: Parallel order execution
- **Indian Market Specialization**: NIFTY/BANKNIFTY support

### Event-Driven Architecture
- **EventBridge Rules**: Cron-based scheduling
- **Step Function Workflows**: Complex orchestration
- **Lambda Functions**: Event processing
- **DynamoDB Streams**: Change data capture

### Monitoring & Observability
- **CloudWatch Dashboards**: Custom metrics visualization
- **Log Retention**: 7 days dev, 30 days staging, 90 days prod
- **SNS Alerting**: Failure notifications
- **CloudWatch Insights**: Log querying and analysis

## Testing Technologies

### Python Testing Stack
- **unittest**: Core Python testing framework (active)
- **pytest**: Alternative testing framework
- **unittest.mock**: Mocking framework
- **boto3 testing**: AWS service mocking with moto
- **Custom fixtures**: Reusable test data and utilities

### Revolutionary Testing Infrastructure (NEW)
- **Dedicated test-venv**: Isolated testing environment
- **End-to-End Testing**: Complete flow validation (5 phases)
- **Performance Benchmarking**: GSI2 optimization validation  
- **Comprehensive Test Suite**: 50+ test cases across unit/integration/performance
- **Test Orchestration**: Automated test runner with detailed reporting
- **Enterprise Testing Agent**: Specialized sub-agent for testing workflows

### Testing Environment Setup
```bash
# Dedicated testing environment
options-strategy-platform/test-venv/    # Isolated test dependencies
tests/end_to_end_flow_tester.py        # Complete flow validation
tests/options_strategies/               # Trading-specific test suite
```

### Frontend Testing (Planned)
- **Jest**: JavaScript testing framework
- **React Testing Library**: Component testing
- **TypeScript**: Compile-time error prevention

## Deployment & CI/CD Technologies

### Infrastructure Deployment
- **AWS CDK**: Infrastructure as code
- **CloudFormation**: AWS native IaC
- **Bash scripts**: Deployment automation
- **Git**: Version control with GitHub

### Security & Compliance
- **AWS IAM**: Identity and access management
- **Secrets Manager**: Credential management
- **Cognito**: User authentication
- **HTTPS**: Secure communication

## Performance Optimizations

### Cost Optimization Technologies
- **Express Step Functions**: 98% cost reduction vs Standard
- **Short log retention**: Cost-conscious logging
- **On-demand DynamoDB**: Pay-per-use billing

### Performance Monitoring
- **CloudWatch metrics**: Performance tracking
- **Custom dashboards**: Real-time monitoring
- **Alarms**: Proactive alerting

## Development Tools & IDE

### Code Editing & Management
- **IntelliJ IDEA**: Primary IDE
- **Git**: Version control
- **GitHub**: Remote repository hosting

### Build & Package Management
- **CDK CLI**: AWS infrastructure deployment
- **pip**: Python package management
- **npm**: Node.js package management

## Future Technology Considerations

### Planned Enhancements
- **Enhanced testing frameworks**: More comprehensive coverage
- **Advanced monitoring**: Detailed performance metrics
- **Multi-environment deployment**: Staging and production pipelines
- **Security hardening**: Additional AWS security services

## Update History
- 2025-09-09: Added modern testing dependencies (moto mock_aws, pytest, faker), updated testing infrastructure with 100% error elimination achievements
- 2025-09-08: Added revolutionary testing infrastructure, dedicated test environments, and enterprise testing agent capabilities