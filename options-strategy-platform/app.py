#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from cdk_stack.options_trading_stack import OptionsTradeStack
from cdk_stack.marketplace_stack import MarketplaceStack

# Load shared configuration from root level
shared_config_path = os.path.join(os.path.dirname(__file__), '..', 'shared_config', 'environments.json')
with open(shared_config_path, 'r') as f:
    config = json.load(f)

# Get environment from context or environment variable
app = cdk.App()
environment = app.node.try_get_context('environment') or os.getenv('QL_ENVIRONMENT', 'dev')

# Validate environment
if environment not in config['environments']:
    raise ValueError(f"Invalid environment: {environment}. Must be one of: {list(config['environments'].keys())}")

# Stack names
auth_stack_name = f"ql-algo-trading-{environment}-auth-broker-stack"
options_stack_name = f"ql-algo-trading-{environment}-options-trading-stack"
marketplace_stack_name = f"ql-algo-trading-{environment}-marketplace-stack"

# Environment configuration for CDK
cdk_env = cdk.Environment(
    account=os.getenv('CDK_DEFAULT_ACCOUNT'),
    region=os.getenv('CDK_DEFAULT_REGION', config['aws']['default_region'])
)

# Create Options Trading Stack
options_stack = OptionsTradeStack(
    app,
    options_stack_name,
    deploy_env=environment,
    config=config,
    auth_stack_name=auth_stack_name,  # For cross-stack references
    env=cdk_env,
    description=f"Quantleap Analytics Options Trading Platform - {environment.title()} Environment"
)

# Create Marketplace Stack (depends on options trading stack for table references)
marketplace_stack = MarketplaceStack(
    app,
    marketplace_stack_name,
    deploy_env=environment,
    config=config,
    auth_stack_name=auth_stack_name,
    options_stack_name=options_stack_name,
    env=cdk_env,
    description=f"Quantleap Analytics Marketplace Platform - {environment.title()} Environment"
)

# Marketplace stack depends on options trading stack (for table exports)
marketplace_stack.add_dependency(options_stack)

app.synth()
