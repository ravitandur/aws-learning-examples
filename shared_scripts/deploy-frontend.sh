#!/bin/bash

# Frontend Build and Deployment Script
# Builds React app and syncs to S3, then invalidates CloudFront cache
#
# Usage: ./deploy-frontend.sh -e {dev|staging|production} -a AWS_PROFILE

set -e

ENVIRONMENT=""
AWS_PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
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
            echo "Usage: $0 -e|--environment {dev|staging|production} -a|--aws-profile PROFILE"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [ -z "$ENVIRONMENT" ] || [ -z "$AWS_PROFILE" ]; then
    echo "Error: All parameters are required"
    echo ""
    echo "Usage: $0 -e|--environment {dev|staging|production} -a|--aws-profile PROFILE"
    echo ""
    echo "Example: $0 -e dev -a account2"
    exit 1
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
    echo "Error: Environment must be one of: dev, staging, production"
    exit 1
fi

# Get script and project directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$( dirname "$SCRIPT_DIR" )"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "=========================================="
echo "🚀 Frontend Build and Deploy"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "AWS Profile: $AWS_PROFILE"
echo "Frontend Directory: $FRONTEND_DIR"
echo ""

# Validate frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Validate AWS profile
echo "Validating AWS profile: $AWS_PROFILE"
if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    echo "Error: AWS profile '$AWS_PROFILE' does not exist"
    exit 1
fi

# Test credentials
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" >/dev/null 2>&1; then
    echo "Error: Invalid credentials for AWS profile '$AWS_PROFILE'"
    exit 1
fi

PROFILE_FLAG="--profile $AWS_PROFILE"
STACK_NAME="ql-algo-trading-${ENVIRONMENT}-frontend-hosting-stack"

echo "✅ AWS Configuration validated"
echo ""

# Get stack outputs
echo "📋 Retrieving infrastructure details..."

BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text \
    $PROFILE_FLAG 2>/dev/null)

CF_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
    --output text \
    $PROFILE_FLAG 2>/dev/null)

CF_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDomainName`].OutputValue' \
    --output text \
    $PROFILE_FLAG 2>/dev/null)

if [ -z "$BUCKET_NAME" ] || [ "$BUCKET_NAME" == "None" ]; then
    echo "Error: Could not retrieve S3 bucket name. Is the infrastructure deployed?"
    echo "Run: ./deploy.sh -p frontend-infrastructure -e $ENVIRONMENT -a $AWS_PROFILE"
    exit 1
fi

if [ -z "$CF_DISTRIBUTION_ID" ] || [ "$CF_DISTRIBUTION_ID" == "None" ]; then
    echo "Error: Could not retrieve CloudFront distribution ID."
    exit 1
fi

echo "   S3 Bucket: $BUCKET_NAME"
echo "   CloudFront Distribution: $CF_DISTRIBUTION_ID"
echo "   CloudFront Domain: $CF_DOMAIN"
echo ""

# Change to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies
echo "📦 Installing dependencies..."
npm ci

# Build frontend
echo ""
echo "🔨 Building frontend for $ENVIRONMENT environment..."
REACT_APP_ENVIRONMENT=$ENVIRONMENT npm run build

if [ ! -d "build" ]; then
    echo "Error: Build directory not created"
    exit 1
fi

echo "✅ Build completed"
echo ""

# Sync static assets with long cache (1 year)
echo "📤 Syncing static assets to S3..."
aws s3 sync build/ "s3://$BUCKET_NAME/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "asset-manifest.json" \
    --exclude "*.map" \
    $PROFILE_FLAG

# Upload index.html with no cache
echo "📤 Uploading index.html (no-cache)..."
aws s3 cp build/index.html "s3://$BUCKET_NAME/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html" \
    $PROFILE_FLAG

# Upload asset-manifest.json with short cache
echo "📤 Uploading asset-manifest.json..."
aws s3 cp build/asset-manifest.json "s3://$BUCKET_NAME/asset-manifest.json" \
    --cache-control "public, max-age=60" \
    --content-type "application/json" \
    $PROFILE_FLAG

echo "✅ S3 sync completed"
echo ""

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CF_DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text \
    $PROFILE_FLAG)

echo "   Invalidation ID: $INVALIDATION_ID"
echo ""

# Success message
echo "=========================================="
echo "✅ Frontend deployed successfully!"
echo "=========================================="
echo ""
echo "🌐 Your application is available at:"
echo "   https://$CF_DOMAIN"
echo ""
echo "📊 CloudFront Distribution: $CF_DISTRIBUTION_ID"
echo "📦 S3 Bucket: $BUCKET_NAME"
echo ""
echo "Note: CloudFront cache invalidation may take a few minutes to propagate."
echo ""
