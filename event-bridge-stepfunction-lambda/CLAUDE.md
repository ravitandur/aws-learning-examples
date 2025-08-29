# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS CDK project implementing an event-driven workflow using EventBridge, Express Step Functions, and Lambda functions. The architecture demonstrates scheduled execution with a 2-minute delay using Step Function Wait states.

**🚀 Status**: Currently deployed and operational in AWS account `142649403032` (ap-south-1)
**📊 Monitoring**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=EventBridge-StepFunction-Lambda-Dashboard)

## Key Commands

### Deployment
- `./deploy.sh -p AWS_PROFILE_NAME` - Deploy stack with mandatory AWS profile validation
- `source venv/bin/activate && cdk synth` - Synthesize CloudFormation templates
- `source venv/bin/activate && cdk destroy` - Clean up resources

### Testing the Workflow
- `aws lambda invoke --function-name EventBridgeStepFunctionSt-EventGeneratorFunctionA1-1ssCPKx1uHV6 response.json --profile account2` - Trigger workflow with deployed function
- View execution logs in CloudWatch Log Group: `/aws/stepfunctions/WaitAndInvokeStateMachine`
- Monitor Step Function: `WaitAndInvokeStateMachine6463445A-lDc86b4pUV96`

### Virtual Environment Management
- Always activate the virtual environment: `source venv/bin/activate`
- Dependencies are in `requirements.txt` at project root

## Architecture Details

### Core Components
1. **Event Generator Lambda** (`lambda_functions/event_generator/`) - Generates EventBridge events with future timestamps (2 minutes ahead) using IST timezone but converting to UTC for AWS services
2. **Express Step Function** - Waits until scheduled time using `TimestampPath` and invokes Time Printer Lambda
3. **Time Printer Lambda** (`lambda_functions/time_printer/`) - Executes at scheduled time and logs execution details
4. **EventBridge Rule** - Matches events from source `custom.event.generator` with detail type `Scheduled Lambda Event`

### Key Design Decisions
- **Express Workflows**: Optimized for high-volume processing (cost: ~$45/month vs $280/month for Standard)
- **IST Timezone Handling**: Event Generator displays IST times but converts to UTC using `isoformat().replace('+00:00', 'Z')` for Step Functions compatibility
- **Mandatory AWS Profile**: `deploy.sh` requires explicit AWS profile to prevent accidental deployments

### CDK Stack Structure
- Main stack: `cdk_stack/event_bridge_stepfunction_stack.py`
- Step Function definition: `step_functions/wait_and_invoke_definition.json`
- Lambda ARN substitution: `${TimePrinterLambdaArn}` placeholder replaced during deployment

### Monitoring and Alerting
The stack includes comprehensive CloudWatch monitoring:
- **Dashboard**: `EventBridge-StepFunction-Lambda-Dashboard`
- **Alarms**: High failure rate, execution volume, Lambda errors, EventBridge failures  
- **SNS Topic**: `step-function-alerts` for notifications
- **Log Retention**: 7 days for Step Function execution logs
- **Custom Metrics**: Log-based metrics for execution tracking

## Important Notes

### Timezone Handling
The system uses a dual-timezone approach:
- IST (UTC+5:30) for display and logging
- UTC for AWS service communication (EventBridge, Step Functions)

### Cost Optimization
Express Workflows provide 98% cost savings for high-volume scenarios. The 5-minute timeout is sufficient for the 2-minute wait workflow.

### Profile Validation
The deployment script validates AWS profile existence, credentials, and displays target account/region before deployment to prevent mistakes.

### Monitoring Access
After deployment, access monitoring via CDK outputs:
- Dashboard URL in stack outputs
- CloudWatch Insights queries provided in outputs
- SNS Topic ARN for alert subscriptions