# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

**GitHub Repository**: https://github.com/ravitandur/aws-learning-examples

This repository contains multiple AWS learning projects demonstrating various serverless architectures, event-driven patterns, and AWS service integrations using AWS CDK. Currently deployed and operational in AWS account `142649403032`.

## Shared Configuration

### AWS Profile
- **Primary deployment profile**: `account2`
- **Account ID**: `142649403032`
- **Primary region**: `ap-south-1`

### Common Commands

#### Repository Management
- `git status` - Check repository status across all projects
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes
- `git push origin main` - Push to GitHub repository

#### CDK Operations (run from project directories)
- `source venv/bin/activate` - Activate Python virtual environment
- `./deploy.sh -p account2` - Deploy with validation and monitoring
- `cdk synth` - Synthesize CloudFormation templates
- `cdk destroy --profile account2` - Clean up resources

#### Testing Workflows
- Each project includes specific testing commands in its CLAUDE.md
- Monitor deployments via CloudWatch dashboards
- Use CloudWatch Insights queries for troubleshooting

## Project Structure

Each project follows this pattern:
- Individual `CLAUDE.md` with project-specific guidance
- CDK stack with Express Workflows (optimized for cost)
- Comprehensive monitoring and alerting
- Deployment scripts with AWS profile validation

## Development Patterns

### Cost Optimization
- Prefer Express Step Functions over Standard (98% cost savings)
- Use short log retention periods (7 days for learning projects)
- Include high-volume execution alarms to prevent cost surprises

### Security & Deployment
- Mandatory AWS profile validation in deployment scripts
- No hardcoded credentials or account IDs in code
- Environment-specific configuration via CDK context

### Monitoring Standards
- CloudWatch dashboards for all deployments
- SNS topics for alerting (subscribe manually for notifications)
- Pre-built CloudWatch Insights queries for troubleshooting

## Frontend Development Standards

### Layout Patterns
All React pages MUST follow the algo-platform layout pattern for consistency:

```tsx
const PageComponent: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Page Title</h1>
      
      {/* Content sections with space-y-6 spacing */}
      <div className="grid...">...</div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">...</div>
    </div>
  );
};
```

**Key Requirements**:
- Root container: `<div className="space-y-6">` (no width constraints)
- Page titles: `text-2xl font-bold` (never text-3xl)
- Section spacing: `space-y-6` between major sections
- Cards: `bg-white dark:bg-gray-800 rounded-lg shadow`
- Responsive: Layout component handles padding with `p-4 sm:p-6 lg:p-8`

### Design System Standards
- **Framework**: React + TypeScript + TailwindCSS
- **Colors**: Blue primary (`blue-600`) with full dark mode support
- **Typography**: Inter font, consistent text sizing
- **Components**: Rounded corners (`rounded-lg`), shadow effects
- **Icons**: Lucide React icons (Turtle icon for branding)
- **Form inputs**: `bg-white dark:bg-gray-700` with proper borders
- **Interactive elements**: Consistent hover states and focus rings

### Authentication Integration
- JWT tokens with auto-refresh functionality
- Context-based state management for user auth
- Indian market specialization (phone validation, states)
- Secure credential handling for broker APIs
- Enhanced broker account management with OAuth integration
- frontend-amplify module/folder in current root project is only experimental, so going forward don't search or do any analysis in this folder. Don't use this folder for any of the context required.

## Latest Enterprise Standards & CDK Compliance (September 2, 2025)

### ✅ Critical LogGroup Pattern Fix - Enterprise Deployment Reliability
**Major Achievement**: Resolved "LogGroup already exists" errors preventing reliable stack redeployments across all environments

#### **Problem Identified & Root Cause**:
- **Issue**: Explicit LogGroup creation with `log_group` parameter caused deployment failures
- **Error**: "LogGroup already exists" errors on stack redeploy, especially in staging/production environments
- **Root Cause**: CDK doesn't handle LogGroup deletion/recreation reliably with removal policies (DESTROY/RETAIN)
- **Impact**: Prevented reliable CI/CD pipelines and required manual LogGroup cleanup

#### **Enterprise Solution Implemented**:
1. **Reverted to logRetention Pattern**:
   - **Updated CDK Stack Creation Agent** to recommend `logRetention` parameter over explicit LogGroups
   - **Reasoning**: Prevents redeploy errors while maintaining same functionality and enterprise compliance
   - **Trade-off**: Shows deprecation warning but ensures reliable deployments across all environments

2. **Both Stacks Updated**:
   - **User-Auth-Broker Stack**: Removed 9 explicit LogGroup constructs, updated all Lambda functions
   - **Options Strategy Stack**: Removed 16 explicit LogGroup constructs, updated all Lambda functions
   - **Pattern**: Simple `log_retention=logs.RetentionDays.ONE_WEEK` parameter
   - **Result**: `Custom::LogRetention` resources handle LogGroup lifecycle properly

3. **Enterprise Standards Maintained**:
   - **Environment-Specific Retention**: 7 days (dev), 30 days (staging), 90 days (production)
   - **Python 3.11 Runtime**: All Lambda functions continue to use modern runtime
   - **Module-Prefix Naming**: Consistent resource naming patterns maintained
   - **Configuration-Driven**: All values continue from shared environments.json

#### **Deployment Success Metrics**:
- ✅ **Dev Environment**: Clean destroy/redeploy capability verified for both stacks
- ✅ **Staging/Production**: No more manual LogGroup cleanup required
- ✅ **Cross-Stack Integration**: Options stack successfully imports from auth stack
- ✅ **Enterprise Reliability**: Both stacks ready for production CI/CD pipelines

### ✅ CDK Stack Creation Agent Updated
**Location**: `.claude/agents/cdk_stack_creation_agent.md`

**Updated Principles**:
1. **Reliable Deployment Pattern**: Use `logRetention` parameter for Lambda functions
2. **Zero Hardcoded Values**: Company prefixes, project names from configuration
3. **Python 3.11 Runtime**: Standard runtime enforcement across all functions
4. **Module-Prefix Naming**: Consistent patterns for resource identification
5. **Configuration-Driven Design**: Environment-specific values from shared_config/environments.json

**New Validation Checklist**:
- ✅ **logRetention Used**: All Lambda functions use logRetention parameter (not explicit LogGroups)
- ✅ **Python 3.11 Runtime**: All functions use modern runtime
- ✅ **Module Prefix Pattern**: All construct IDs follow consistent naming
- ✅ **Resource Name Pattern**: All resource names follow {module-prefix}-{function-name}
- ✅ **Deployment Reliability**: Stacks can be destroyed and redeployed without errors

## Latest Project Updates (September 2, 2025)

### ✅ Complete Two-Stack Architecture Deployment
**Major Achievement**: Successfully deployed both stacks with enterprise-grade reliability patterns

#### **Stack 1: User Authentication & Broker Management**
- **Status**: ✅ Deployed and operational
- **Stack Name**: `ql-algo-trading-dev-auth-broker-stack`
- **API Gateway**: `https://4fhetaydtg.execute-api.ap-south-1.amazonaws.com/dev/`
- **Infrastructure**: 9 Lambda functions, 2 DynamoDB tables, Cognito User Pool, Secrets Manager

#### **Stack 2: Options Strategy Platform**
- **Status**: ✅ Deployed and operational
- **Stack Name**: `ql-algo-trading-dev-options-trading-stack`
- **API Gateway**: `https://2f8bmi4edb.execute-api.ap-south-1.amazonaws.com/dev/`
- **Infrastructure**: 16 Lambda functions, 9 DynamoDB tables, cross-stack integration

#### **Enterprise Reliability Fixes Applied**:
1. **LogGroup Pattern Resolution**:
   - **Problem**: Explicit LogGroup creation caused "LogGroup already exists" errors on redeploy
   - **Solution**: Reverted to `logRetention` parameter for reliable stack lifecycle management
   - **Result**: Both stacks can now be destroyed and redeployed without manual cleanup

2. **CDK Stack Creation Agent Updates**:
   - **Updated**: CDK best practices to prevent redeploy issues
   - **Pattern**: `logRetention` parameter instead of explicit LogGroup constructs
   - **Benefit**: `Custom::LogRetention` resources handle LogGroup lifecycle automatically

3. **Cross-Stack Integration Verified**:
   - **Options Stack** successfully imports UserPoolId and BrokerAccountsTable from Auth Stack
   - **Shared API Gateway**: Both stacks extend the same API Gateway with different endpoints
   - **Environment Configuration**: All resources use shared environments.json configuration

#### **Frontend Integration Completed**:
- **Environment Variables**: Updated with both API Gateway endpoints
- **Multi-API Architecture**: Auth API and Options API configured separately
- **Development Server**: Running at `http://localhost:3000` with hot reload
- **TypeScript Compilation**: Clean build with comprehensive type safety

#### **Revolutionary Features Now Available**:
1. **Strategy-Specific Broker Allocation**: Each strategy can use different brokers with custom lot distributions
2. **Complete Options Platform**: 9-table database architecture with execution engine
3. **Cross-Stack Authentication**: Seamless user authentication across both platforms
4. **Indian Market Integration**: Native support for NIFTY, BANKNIFTY with proper expiry handling
5. **Admin Marketplace**: Professional strategies available for user subscription

#### **Current Deployment Status**:
- **Both Stacks**: ✅ Deployed with logRetention pattern for reliable redeployment
- **Frontend**: ✅ Updated with dual API configuration
- **Cross-Stack**: ✅ Verified integration between auth and options platforms
- **Documentation**: ✅ All CLAUDE.md files updated with current deployment information