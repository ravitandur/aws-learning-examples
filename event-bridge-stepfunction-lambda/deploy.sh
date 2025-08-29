#!/bin/bash

# Deployment script for EventBridge-StepFunction-Lambda stack

# Parse command line arguments
AWS_PROFILE=""
while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-p|--profile AWS_PROFILE_NAME]"
      exit 1
      ;;
  esac
done

# Require profile - exit if not provided
if [ -z "$AWS_PROFILE" ]; then
    echo "Error: AWS Profile is mandatory for deployment"
    echo "Available profiles:"
    aws configure list-profiles 2>/dev/null || echo "No profiles found."
    echo ""
    echo "Usage: $0 -p|--profile AWS_PROFILE_NAME"
    echo "Example: $0 -p my-aws-profile"
    exit 1
fi

echo "Starting deployment of EventBridge-StepFunction-Lambda stack..."

# Validate AWS profile exists
echo "Validating AWS profile: $AWS_PROFILE"
if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    echo "Error: AWS profile '$AWS_PROFILE' does not exist"
    echo "Available profiles:"
    aws configure list-profiles
    exit 1
fi

# Test profile credentials
echo "Testing credentials for profile: $AWS_PROFILE"
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" >/dev/null 2>&1; then
    echo "Error: Invalid credentials for AWS profile '$AWS_PROFILE'"
    exit 1
fi

# Set profile for subsequent commands
export AWS_PROFILE="$AWS_PROFILE"
PROFILE_FLAG="--profile $AWS_PROFILE"
echo "Using AWS profile: $AWS_PROFILE"

# Display account and region info
echo "Account ID: $(aws sts get-caller-identity --query Account --output text $PROFILE_FLAG)"
echo "Region: $(aws configure get region $PROFILE_FLAG || echo 'us-east-1 (default)')"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Bootstrap CDK if not already done
echo "Bootstrapping CDK (if needed)..."
cdk bootstrap $PROFILE_FLAG

# Deploy the stack
echo "Deploying CDK stack..."
cdk deploy --require-approval never $PROFILE_FLAG

echo "Deployment completed!"
echo ""
echo "To test the workflow:"
echo "1. Invoke the Event Generator Lambda function using AWS CLI:"
echo "   aws lambda invoke --function-name EventBridgeStepFunctionStack-EventGeneratorFunction* response.json --profile $AWS_PROFILE"
echo "2. Check the Step Function executions in AWS Console"
echo "3. Check CloudWatch Logs for Lambda Function 2 execution after 2 minutes"
echo ""
echo "Note: The Event Generator Lambda uses IST timezone for display but converts to UTC for EventBridge scheduling."