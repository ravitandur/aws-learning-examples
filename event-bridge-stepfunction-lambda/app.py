#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_stack.event_bridge_stepfunction_stack import EventBridgeStepFunctionStack

app = cdk.App()
EventBridgeStepFunctionStack(app, "EventBridgeStepFunctionStack",
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION', 'ap-south-1')
    )
)

app.synth()