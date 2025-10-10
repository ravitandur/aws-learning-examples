#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk
from cdk_stack.user_auth_broker_stack import UserAuthBrokerStack

# Load environment configuration from shared config
config_path = os.path.join(os.path.dirname(__file__), '..', 'shared_config', 'environments.json')
with open(config_path, 'r') as f:
    config = json.load(f)

# Get environment from context or environment variable
app = cdk.App()
environment = app.node.try_get_context('environment') or os.getenv('QL_ENVIRONMENT', 'dev')

# Validate environment
if environment not in config['environments']:
    raise ValueError(f"Invalid environment: {environment}. Must be one of: {list(config['environments'].keys())}")

# Create stack with environment and module-specific naming
stack_name = f"ql-algo-trading-{environment}-auth-broker-stack"

UserAuthBrokerStack(
    app, 
    stack_name,
    deploy_env=environment,
    config=config,
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', config['aws']['default_region'])
    ),
    description=f"Quantleap Analytics Algo Trading Platform - {environment.title()} Environment - Module 2"
)

app.synth()