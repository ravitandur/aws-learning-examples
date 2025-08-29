# EventBridge-StepFunction-Lambda Workflow

**🔗 GitHub Repository**: https://github.com/ravitandur/aws-learning-examples  
**🚀 Status**: ✅ **Currently Deployed** to AWS Account `142649403032` (ap-south-1)  
**📊 Monitoring**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:name=EventBridge-StepFunction-Lambda-Dashboard)

This project demonstrates an event-driven workflow using AWS EventBridge, Express Step Functions, and Lambda functions with comprehensive monitoring and cost optimization.

## Architecture Flow

1. **Lambda Function 1 (Event Generator)** - Generates events with future timestamps (2 minutes from current IST time) and sends them to EventBridge
2. **EventBridge** - Matches the rule and triggers Step Function
3. **Step Function** - Waits until the scheduled time and then invokes Lambda Function 2
4. **Lambda Function 2 (Time Printer)** - Prints the current time when executed

## Project Structure

```
event-bridge-stepfunction-lambda/
├── lambda_functions/
│   ├── event_generator/
│   │   ├── lambda_function.py      # Generates EventBridge events
│   │   └── requirements.txt
│   └── time_printer/
│       ├── lambda_function.py      # Prints current time
│       └── requirements.txt
├── step_functions/
│   └── wait_and_invoke_definition.json  # Step Function definition
├── cdk_stack/
│   ├── __init__.py
│   └── event_bridge_stepfunction_stack.py  # CDK stack definition
├── venv/                           # Virtual environment
├── app.py                          # CDK app entry point
├── cdk.json                        # CDK configuration
├── requirements.txt                # Python dependencies
├── deploy.sh                       # Deployment script
└── .gitignore
```

## Prerequisites

- AWS CLI configured with your credentials
- Python 3.9 or later
- Node.js (for AWS CDK)
- AWS CDK installed globally: `npm install -g aws-cdk`

## Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd event-bridge-stepfunction-lambda
   ```

2. **Set up AWS credentials:**
   ```bash
   aws configure
   # Enter your aws_access_key_id, aws_secret_access_key, and region
   ```

3. **Run the deployment script:**
   ```bash
   ./deploy.sh -p account2
   ```
   
   This script will:
   - Create/activate virtual environment
   - Install Python dependencies
   - Bootstrap CDK (if needed)
   - Deploy the stack

## Manual Setup (Alternative)

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Bootstrap CDK:**
   ```bash
   cdk bootstrap
   ```

4. **Deploy the stack:**
   ```bash
   cdk deploy
   ```

## Testing the Workflow

1. **Trigger the workflow by invoking Lambda Function 1:**
   ```bash
   aws lambda invoke --function-name EventBridgeStepFunctionSt-EventGeneratorFunctionA1-1ssCPKx1uHV6 response.json --profile account2
   cat response.json
   ```

2. **Monitor the execution:**
   - Check Step Function executions in AWS Console
   - Check CloudWatch Logs for both Lambda functions
   - The Time Printer Lambda will execute 2 minutes after the Event Generator

## Key Features

- **Express Step Functions**: 98% cost optimization (~$45/month vs $280/month for Standard)
- **IST Timezone Support**: Event Generator uses Indian Standard Time for display
- **UTC Conversion**: Automatically converts to UTC for EventBridge/Step Functions compatibility
- **Comprehensive Monitoring**: CloudWatch Dashboard, alarms, and SNS alerts
- **Cost Protection**: High-volume execution alarms to prevent surprise bills
- **Error Handling**: Includes retry logic in Step Functions and error handling in Lambda functions
- **Profile Validation**: Mandatory AWS profile verification in deployment script

## Clean Up

To avoid AWS charges, destroy the stack when done:
```bash
cdk destroy
```

## Troubleshooting

- If deployment fails, check AWS credentials and permissions
- Ensure your AWS account has sufficient permissions for Lambda, Step Functions, EventBridge, and IAM
- Check CloudWatch Logs for Lambda execution details
- Verify Step Function execution in AWS Console