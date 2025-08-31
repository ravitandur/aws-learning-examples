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

## Latest Project Updates (August 30, 2025)

### ✅ Enhanced Broker Account Management System
**Major Enhancement**: Complete redesign of broker account data structure with OAuth integration

#### **Key Improvements**:
- **Natural Key Design**: Replaced UUID broker_account_id with client_id as sort key
- **Enhanced Data Model**: Added group classification (BFW/KOU/PMS), capital tracking, descriptions
- **OAuth Architecture**: Implemented daily trading session management for Zerodha
- **Dual Storage Pattern**: Separate Secrets Manager storage for API credentials vs OAuth tokens
- **Multi-Broker Support**: Zerodha, Angel One, Finvasia, Zebu with broker-specific validations
- **Field Restrictions**: Immutable fields (broker_name, client_id) vs editable fields (capital, credentials)

#### **Technical Achievements**:
- **DynamoDB Decimal Handling**: Custom JSON encoder for financial data types
- **API Gateway Restructure**: Updated to use {client_id} path parameters
- **Frontend Migration**: Complete TypeScript interface updates and component migration
- **Environment Configuration**: Proper .env setup with new API Gateway endpoints
- **OAuth Infrastructure**: Lambda functions and API endpoints ready for trading session management

#### **Current Deployment Status**:
- **API Gateway**: `https://cgsdoaq0i1.execute-api.ap-south-1.amazonaws.com/dev/`
- **Frontend**: Running at `http://localhost:3000` with updated configuration
- **Backend**: All Lambda functions deployed with enhanced data model
- **Testing**: Ready for complete broker account workflow validation