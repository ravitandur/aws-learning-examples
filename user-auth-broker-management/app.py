#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_stack.user_auth_broker_stack import UserAuthBrokerStack

app = cdk.App()
UserAuthBrokerStack(app, "UserAuthBrokerStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'ap-south-1')
    ),
    description="User Authentication and Broker Management for Algorithmic Trading Platform - Module 2"
)

app.synth()