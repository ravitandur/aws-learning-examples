#!/bin/bash

# Deployment script for User Authentication & Broker Management stack

# Parse command line arguments
AWS_PROFILE=""
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -p|--profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 -e|--environment {dev|staging|production} -p|--profile AWS_PROFILE_NAME"
      exit 1
      ;;
  esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    echo "Error: Environment must be one of: dev, staging, production"
    echo ""
    echo "Usage: $0 -e|--environment {dev|staging|production} -p|--profile AWS_PROFILE_NAME"
    echo "Example: $0 -e dev -p account2"
    exit 1
fi

# Require profile - exit if not provided
if [ -z "$AWS_PROFILE" ]; then
    echo "Error: AWS Profile is mandatory for deployment"
    echo "Available profiles:"
    aws configure list-profiles 2>/dev/null || echo "No profiles found."
    echo ""
    echo "Usage: $0 -e|--environment {dev|staging|production} -p|--profile AWS_PROFILE_NAME"
    echo "Example: $0 -e dev -p account2"
    exit 1
fi

echo "Starting deployment of Quantleap Analytics Algorithmic Trading Platform"
echo "Environment: $ENVIRONMENT"
echo "AWS Profile: $AWS_PROFILE"
echo "Target: Module 2 - User Authentication & Broker Management"
echo ""

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

# Set environment variables for CDK
export AWS_PROFILE="$AWS_PROFILE"
export QL_ENVIRONMENT="$ENVIRONMENT"
PROFILE_FLAG="--profile $AWS_PROFILE"
echo "Using AWS profile: $AWS_PROFILE"
echo "Deploying to environment: $ENVIRONMENT"

# Display account and region info
echo "Account ID: $(aws sts get-caller-identity --query Account --output text $PROFILE_FLAG)"
echo "Region: $(aws configure get region $PROFILE_FLAG || echo 'ap-south-1 (default)')"
echo ""

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Lambda dependencies are handled by CDK during deployment
# CDK will automatically bundle requirements.txt dependencies
echo "🚀 Lambda dependencies will be handled by CDK bundling..."
echo "📦 CDK will:"
echo "   • Read each Lambda's requirements.txt"  
echo "   • Install dependencies in isolated environment"
echo "   • Package them separately from source code"
echo "   • Keep Lambda directories clean in git"

# Copy validators to Lambda functions that need them
echo "Copying Indian validators to Lambda functions..."
cp -r lambda_functions/validators lambda_functions/auth/ 2>/dev/null || true
cp lambda_functions/validators/indian_validators.py lambda_functions/auth/ 2>/dev/null || true

# Copy shared utilities to Lambda functions
echo "Copying shared utilities to Lambda functions..."
cp -r ../shared_utils lambda_functions/auth/ 2>/dev/null || true
cp -r ../shared_utils lambda_functions/broker_accounts/ 2>/dev/null || true

# Bootstrap CDK if not already done
echo "Bootstrapping CDK (if needed)..."
cdk bootstrap $PROFILE_FLAG

echo ""
echo "Synthesizing CDK stack for $ENVIRONMENT environment..."
cdk synth --context environment=$ENVIRONMENT $PROFILE_FLAG

echo ""
echo "Deploying CDK stack to $ENVIRONMENT environment..."
cdk deploy "ql-algo-trading-${ENVIRONMENT}-stack" \
  --context environment=$ENVIRONMENT \
  --require-approval never \
  $PROFILE_FLAG

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "🎯 Quantleap Analytics Algo Trading Platform - $ENVIRONMENT Environment"
    echo "📦 Stack: ql-algo-trading-${ENVIRONMENT}-stack"
    echo ""
    echo "📋 What was deployed:"
    echo "   • Cognito User Pool: ql-algo-trading-${ENVIRONMENT}-users"
    echo "   • DynamoDB Tables: ql-algo-trading-${ENVIRONMENT}-user-profiles, ql-algo-trading-${ENVIRONMENT}-broker-accounts"
    echo "   • Lambda Functions: ql-algo-trading-${ENVIRONMENT}-user-registration, ql-algo-trading-${ENVIRONMENT}-user-auth, ql-algo-trading-${ENVIRONMENT}-broker-accounts"
    echo "   • API Gateway: ql-algo-trading-${ENVIRONMENT}-api"
    echo "   • Secrets Manager: ql-zerodha-credentials-${ENVIRONMENT}-* pattern"
    echo "   • CloudWatch Dashboard with environment-specific metrics"
    echo ""
    echo "🧪 To test the system:"
    echo ""
    echo "1. Register a new user:"
    echo "   curl -X POST https://\$(aws cloudformation describe-stacks --stack-name ql-algo-trading-${ENVIRONMENT}-stack --query 'Stacks[0].Outputs[?OutputKey==\`ApiGatewayUrl\`].OutputValue' --output text $PROFILE_FLAG)auth/register \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{"
    echo "       \"phone_number\": \"+919876543210\","
    echo "       \"email\": \"your@email.com\","
    echo "       \"full_name\": \"Your Full Name\","
    echo "       \"state\": \"Karnataka\","
    echo "       \"password\": \"YourSecurePassword123!\""
    echo "     }'"
    echo ""
    echo "2. Login to get JWT token:"
    echo "   curl -X POST https://\$(aws cloudformation describe-stacks --stack-name ql-algo-trading-${ENVIRONMENT}-stack --query 'Stacks[0].Outputs[?OutputKey==\`ApiGatewayUrl\`].OutputValue' --output text $PROFILE_FLAG)auth/login \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{"
    echo "       \"username\": \"+919876543210\","
    echo "       \"password\": \"YourSecurePassword123!\""
    echo "     }'"
    echo ""
    echo "3. Add your Zerodha account (use JWT token from login):"
    echo "   curl -X POST https://\$(aws cloudformation describe-stacks --stack-name ql-algo-trading-${ENVIRONMENT}-stack --query 'Stacks[0].Outputs[?OutputKey==\`ApiGatewayUrl\`].OutputValue' --output text $PROFILE_FLAG)broker-accounts \\"
    echo "     -H \"Authorization: Bearer YOUR_JWT_TOKEN\" \\"
    echo "     -H \"Content-Type: application/json\" \\"
    echo "     -d '{"
    echo "       \"broker_name\": \"zerodha\","
    echo "       \"api_key\": \"your_zerodha_api_key\","
    echo "       \"api_secret\": \"your_zerodha_api_secret\""
    echo "     }'"
    echo ""
    echo "📊 Monitor your deployment:"
    echo "   AWS Console → CloudWatch → Dashboards → $(echo $ENVIRONMENT | sed 's/dev/Dev/;s/staging/Staging/;s/production/Prod/')-ql-algo-trading-${ENVIRONMENT}-dashboard"
    echo ""
    echo "🎉 Ready for Module 3: Market Data Integration!"
    echo ""
    echo "💡 Note: This module provides the authentication foundation for your"
    echo "   algorithmic trading platform. Your Zerodha credentials are stored"
    echo "   securely in AWS Secrets Manager with encryption."
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Please check the error messages above and try again."
    exit 1
fi