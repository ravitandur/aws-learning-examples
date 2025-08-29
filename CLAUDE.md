# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains multiple AWS learning projects demonstrating various serverless architectures, event-driven patterns, and AWS service integrations using AWS CDK.

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