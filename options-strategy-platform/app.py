#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from cdk_stack.options_trading_stack import OptionsTradeStack

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

# Create stack with enhanced naming for options trading
stack_name = f"ql-algo-trading-{environment}-options-trading-stack"

# Reference existing auth-broker stack outputs
auth_stack_name = f"ql-algo-trading-{environment}-auth-broker-stack"

OptionsTradeStack(
    app, 
    stack_name,
    deploy_env=environment,
    config=config,
    auth_stack_name=auth_stack_name,  # For cross-stack references
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', config['aws']['default_region'])
    ),
    description=f"Quantleap Analytics Options Trading Platform - {environment.title()} Environment"
)

app.synth()