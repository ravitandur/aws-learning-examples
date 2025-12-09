#!/bin/bash

# Universal deployment script for Quantleap Analytics Algorithmic Trading Platform
# Supports multiple project modules with shared configuration

# Parse command line arguments
PROJECT=""
AWS_PROFILE=""
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
  case $1 in
    -p|--project)
      PROJECT="$2"
      shift 2
      ;;
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    -a|--aws-profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 -p|--project PROJECT_NAME -e|--environment {dev|staging|production} -a|--aws-profile AWS_PROFILE_NAME"
      echo "Available projects: user-auth-broker-management, options-strategy-platform"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$PROJECT" ] || [ -z "$ENVIRONMENT" ] || [ -z "$AWS_PROFILE" ]; then
    echo "Error: All parameters are required"
    echo ""
    echo "Usage: $0 -p|--project PROJECT_NAME -e|--environment {dev|staging|production} -a|--aws-profile AWS_PROFILE_NAME"
    echo ""
    echo "Available projects:"
    echo "  • user-auth-broker-management    - User authentication and broker account management"
    echo "  • options-strategy-platform      - Complete options trading platform"
    echo "  • frontend-infrastructure        - React frontend hosting (S3 + CloudFront)"
    echo ""
    echo "Example: $0 -p options-strategy-platform -e dev -a account2"
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    echo "Error: Environment must be one of: dev, staging, production"
    exit 1
fi

# Get script directory (shared_scripts)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"
PROJECT_DIR="$ROOT_DIR/$PROJECT"

# Validate project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory '$PROJECT' does not exist"
    echo "Available projects:"
    ls -d */ | grep -E "(user-auth-broker-management|options-strategy-platform|frontend-infrastructure)" | sed 's/\///g' | sed 's/^/  • /'
    exit 1
fi

echo "=========================================="
echo "🚀 Quantleap Analytics Deployment Script"
echo "=========================================="
echo "Project: $PROJECT"
echo "Environment: $ENVIRONMENT"
echo "AWS Profile: $AWS_PROFILE"
echo "Project Directory: $PROJECT_DIR"
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

# Display account and region info
echo "✅ AWS Configuration:"
echo "   Account ID: $(aws sts get-caller-identity --query Account --output text $PROFILE_FLAG)"
echo "   Region: $(aws configure get region $PROFILE_FLAG || echo 'ap-south-1 (default)')"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Load shared configuration
SHARED_CONFIG="$ROOT_DIR/shared_config/environments.json"
if [ ! -f "$SHARED_CONFIG" ]; then
    echo "Error: Shared configuration file not found: $SHARED_CONFIG"
    exit 1
fi

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found, installing basic CDK dependencies..."
    pip install aws-cdk-lib boto3
fi

# Copy shared utilities to Lambda functions if they exist
if [ -d "lambda_functions" ]; then
    echo "📋 Copying shared utilities to Lambda functions..."
    
    # Find all lambda function directories (simplified approach)
    for lambda_dir in lambda_functions/*/; do
        if [ -d "$lambda_dir" ]; then
            echo "   Copying shared_utils to: $lambda_dir"
            cp -r "$ROOT_DIR/shared_utils" "$lambda_dir/" 2>/dev/null || true
        fi
    done
fi

# Bootstrap CDK if not already done
echo "🔧 Bootstrapping CDK (if needed)..."
cdk bootstrap $PROFILE_FLAG

# Get stack name from shared config based on project
STACK_SUFFIX=""
case "$PROJECT" in
    "user-auth-broker-management")
        STACK_SUFFIX="auth-broker-stack"
        ;;
    "options-strategy-platform")
        STACK_SUFFIX="options-trading-stack"
        ;;
    "frontend-infrastructure")
        STACK_SUFFIX="frontend-hosting-stack"
        ;;
    *)
        echo "Error: Unknown project stack mapping for: $PROJECT"
        exit 1
        ;;
esac

STACK_NAME="ql-algo-trading-${ENVIRONMENT}-${STACK_SUFFIX}"

echo ""
echo "🔨 Synthesizing CDK stack for $ENVIRONMENT environment..."
cdk synth --context environment=$ENVIRONMENT $PROFILE_FLAG

echo ""
echo "🚀 Deploying CDK stack to $ENVIRONMENT environment..."
echo "Stack: $STACK_NAME"

cdk deploy "$STACK_NAME" \
  --context environment=$ENVIRONMENT \
  --require-approval never \
  $PROFILE_FLAG

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "🎯 Quantleap Analytics - $PROJECT ($ENVIRONMENT)"
    echo "📦 Stack: $STACK_NAME"
    echo ""
    
    # Project-specific post-deployment information
    case "$PROJECT" in
        "user-auth-broker-management")
            echo "📋 User Authentication & Broker Management deployed:"
            echo "   • Cognito User Pool with custom attributes"
            echo "   • DynamoDB tables for users and broker accounts"
            echo "   • API Gateway with authentication endpoints"
            echo "   • Lambda functions for user and broker operations"
            echo "   • Secrets Manager for secure credential storage"
            echo ""

            # Get User Pool ID from stack outputs
            USER_POOL_ID=$(aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
                --output text \
                $PROFILE_FLAG 2>/dev/null)

            if [ -n "$USER_POOL_ID" ]; then
                echo "🔐 Cognito User Pool ID: $USER_POOL_ID"
                echo ""
                echo "👤 To add admin users to the Admins group, run:"
                echo "   aws cognito-idp admin-add-user-to-group \\"
                echo "     --user-pool-id $USER_POOL_ID \\"
                echo "     --username YOUR_ADMIN_EMAIL \\"
                echo "     --group-name Admins \\"
                echo "     --profile $AWS_PROFILE"
                echo ""

                # Optional: Prompt to add admin user now
                read -p "Would you like to add an admin user now? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    read -p "Enter admin email: " ADMIN_EMAIL
                    if [ -n "$ADMIN_EMAIL" ]; then
                        echo "Adding $ADMIN_EMAIL to Admins group..."
                        aws cognito-idp admin-add-user-to-group \
                            --user-pool-id "$USER_POOL_ID" \
                            --username "$ADMIN_EMAIL" \
                            --group-name Admins \
                            --profile "$AWS_PROFILE" 2>/dev/null

                        if [ $? -eq 0 ]; then
                            echo "✅ Successfully added $ADMIN_EMAIL to Admins group"
                        else
                            echo "⚠️  User may not exist yet. They will be added to Admins group after first login/signup."
                            echo "   Re-run the command above after user creation."
                        fi
                    fi
                fi
            fi
            ;;
        "options-strategy-platform")
            echo "📋 Options Strategy Platform deployed:"
            echo "   • Complete options trading infrastructure"
            echo "   • Strategy and basket management system"
            echo "   • Multi-broker execution engine"
            echo "   • Real-time market data and position tracking"
            echo "   • Performance analytics and risk management"
            ;;
        "frontend-infrastructure")
            echo "📋 Frontend Hosting Infrastructure deployed:"
            echo "   • S3 bucket for static assets"
            echo "   • CloudFront distribution with HTTPS"
            echo "   • SPA routing configured"
            echo ""

            # Get stack outputs
            BUCKET_NAME=$(aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
                --output text \
                $PROFILE_FLAG 2>/dev/null)

            CF_DOMAIN=$(aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
                --output text \
                $PROFILE_FLAG 2>/dev/null)

            echo "🌐 CloudFront URL: https://$CF_DOMAIN"
            echo "📦 S3 Bucket: $BUCKET_NAME"
            echo ""
            echo "To deploy frontend code, run:"
            echo "   $ROOT_DIR/shared_scripts/deploy-frontend.sh -e $ENVIRONMENT -a $AWS_PROFILE"
            ;;
    esac
    
    echo ""
    echo "📊 Monitor your deployment:"
    echo "   AWS Console → CloudWatch → Dashboards"
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Please check the error messages above and try again."
    exit 1
fi