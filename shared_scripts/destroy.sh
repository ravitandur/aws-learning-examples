#!/bin/bash

# Universal destroy script for Quantleap Analytics Algorithmic Trading Platform
# Safely removes stacks with confirmation

# Parse command line arguments
PROJECT=""
AWS_PROFILE=""
ENVIRONMENT=""
FORCE=false

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
    -f|--force)
      FORCE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 -p|--project PROJECT_NAME -e|--environment {dev|staging|production} -a|--aws-profile AWS_PROFILE_NAME [-f|--force]"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [ -z "$PROJECT" ] || [ -z "$ENVIRONMENT" ] || [ -z "$AWS_PROFILE" ]; then
    echo "Error: All parameters are required"
    echo ""
    echo "Usage: $0 -p|--project PROJECT_NAME -e|--environment {dev|staging|production} -a|--aws-profile AWS_PROFILE_NAME [-f|--force]"
    echo ""
    echo "Available projects:"
    echo "  • user-auth-broker-management    - User authentication and broker account management"
    echo "  • options-strategy-platform      - Complete options trading platform"
    echo ""
    echo "Example: $0 -p options-strategy-platform -e dev -a account2"
    exit 1
fi

# Get stack name
STACK_SUFFIX=""
case "$PROJECT" in
    "user-auth-broker-management")
        STACK_SUFFIX="auth-broker-stack"
        ;;
    "options-strategy-platform")
        STACK_SUFFIX="options-trading-stack"
        ;;
    *)
        echo "Error: Unknown project: $PROJECT"
        exit 1
        ;;
esac

STACK_NAME="ql-algo-trading-${ENVIRONMENT}-${STACK_SUFFIX}"

echo "⚠️  WARNING: You are about to destroy the following stack:"
echo "   Stack: $STACK_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Project: $PROJECT"
echo ""

# Safety check for production
if [ "$ENVIRONMENT" == "production" ] && [ "$FORCE" != true ]; then
    echo "🚨 PRODUCTION ENVIRONMENT DETECTED!"
    echo "   This action will destroy production resources permanently."
    echo "   Use -f|--force flag if you really want to proceed."
    exit 1
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    read -p "Are you sure you want to destroy this stack? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Operation cancelled."
        exit 0
    fi
fi

# Get script directory and project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"
PROJECT_DIR="$ROOT_DIR/$PROJECT"

# Change to project directory
cd "$PROJECT_DIR"

# Set environment variables
export AWS_PROFILE="$AWS_PROFILE"
export QL_ENVIRONMENT="$ENVIRONMENT"
PROFILE_FLAG="--profile $AWS_PROFILE"

echo ""
echo "🔥 Destroying stack: $STACK_NAME"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Destroy the stack
cdk destroy "$STACK_NAME" \
  --context environment=$ENVIRONMENT \
  --force \
  $PROFILE_FLAG

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Stack destroyed successfully!"
    echo "   Stack: $STACK_NAME"
    echo ""
else
    echo ""
    echo "❌ Stack destruction failed!"
    echo "Please check the error messages above."
    exit 1
fi