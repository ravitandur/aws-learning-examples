# AWS Learning Examples

**🔗 Repository**: https://github.com/ravitandur/aws-learning-examples

A collection of hands-on AWS serverless architecture examples built with AWS CDK, demonstrating event-driven patterns, cost-optimized deployments, and comprehensive monitoring.

**📊 Deployed to AWS Account**: `142649403032` (ap-south-1) using profile `account2`

## Projects

### 🚀 EventBridge-StepFunction-Lambda
**Status**: ✅ Complete  
**Architecture**: EventBridge → Express Step Functions → Lambda  
**Features**: IST timezone handling, 2-minute scheduling, comprehensive monitoring  
**Cost**: ~$45/month for 100K executions (Express Workflows optimization)

## Getting Started

### Prerequisites
- AWS CLI configured
- Python 3.9+
- Node.js + AWS CDK (`npm install -g aws-cdk`)
- AWS profile `account2` configured for deployments

### Quick Start
1. **Clone repository**: `git clone https://github.com/ravitandur/aws-learning-examples.git`
2. **Navigate to project**: `cd aws-learning-examples/event-bridge-stepfunction-lambda`
3. **Deploy**: `./deploy.sh -p account2`
4. **Monitor**: Access [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=EventBridge-StepFunction-Lambda-Dashboard)

### Current Deployments
- **EventBridge-StepFunction-Lambda**: ✅ **Live** in `ap-south-1`
  - Event Generator: `EventBridgeStepFunctionSt-EventGeneratorFunctionA1-1ssCPKx1uHV6`
  - Time Printer: `EventBridgeStepFunctionSt-TimePrinterFunctionAD0D2-GFf7lQ7TBpFK`
  - Step Function: `WaitAndInvokeStateMachine6463445A-lDc86b4pUV96`
  - Dashboard: [EventBridge-StepFunction-Lambda-Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=EventBridge-StepFunction-Lambda-Dashboard)

## Repository Structure

```
aws-learning-examples/
├── CLAUDE.md                           # Shared configuration & patterns
├── event-bridge-stepfunction-lambda/   # EventBridge + Step Functions demo
│   ├── CLAUDE.md                       # Project-specific guidance
│   ├── lambda_functions/               # Event generator & time printer
│   ├── step_functions/                 # Workflow definitions
│   └── cdk_stack/                      # Infrastructure as code
└── [future projects]                   # Additional learning examples
```

## Architecture Patterns

- **Express Step Functions** for cost optimization (98% savings vs Standard)
- **Event-driven workflows** with EventBridge integration
- **Timezone-aware scheduling** (IST display, UTC processing)
- **Comprehensive monitoring** with dashboards and alerting
- **Profile-validated deployments** for security

## Monitoring & Operations

Each project includes:
- CloudWatch Dashboard with key metrics
- SNS alerting for failures and high-volume scenarios
- CloudWatch Insights queries for troubleshooting
- Cost protection alarms

## Development Philosophy

- **Learning-focused**: Real-world patterns with educational value
- **Cost-conscious**: Optimized for learning without surprise bills
- **Production-ready**: Includes monitoring, error handling, and security
- **Reusable**: Standardized patterns across projects