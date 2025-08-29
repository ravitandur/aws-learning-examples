from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    CfnOutput
)
from constructs import Construct
import json

class EventBridgeStepFunctionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Function 1: Event Generator
        event_generator_lambda = _lambda.Function(
            self, "EventGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/event_generator"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(30),
            description="Lambda function that generates events with future timestamps for EventBridge"
        )

        # Lambda Function 2: Time Printer
        time_printer_lambda = _lambda.Function(
            self, "TimePrinterFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda_functions/time_printer"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(30),
            description="Lambda function that prints current time when invoked by Step Functions"
        )

        # Grant EventBridge permissions to Event Generator Lambda
        event_generator_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["events:PutEvents"],
                resources=["*"]
            )
        )

        # Load Step Function definition and substitute Lambda ARN
        with open("step_functions/wait_and_invoke_definition.json", "r") as f:
            step_function_definition = f.read()
        
        # Replace the placeholder with actual Lambda ARN
        step_function_definition = step_function_definition.replace(
            "${TimePrinterLambdaArn}", 
            time_printer_lambda.function_arn
        )

        # Create CloudWatch Log Group for Express Step Function
        step_function_log_group = logs.LogGroup(
            self, "StepFunctionLogGroup",
            log_group_name="/aws/stepfunctions/WaitAndInvokeStateMachine",
            retention=logs.RetentionDays.ONE_WEEK
        )

        # Create Express Step Function (optimized for high-volume processing)
        wait_and_invoke_sfn = sfn.StateMachine(
            self, "WaitAndInvokeStateMachine",
            definition_body=sfn.DefinitionBody.from_string(step_function_definition),
            state_machine_type=sfn.StateMachineType.EXPRESS,
            timeout=Duration.minutes(5),
            logs=sfn.LogOptions(
                destination=step_function_log_group,
                level=sfn.LogLevel.ALL
            ),
            comment="Express Step Function that waits until scheduled time and invokes Lambda Function 2 (optimized for high volume)"
        )

        # Grant Step Function permission to invoke Lambda Function 2
        time_printer_lambda.grant_invoke(wait_and_invoke_sfn)

        # Create EventBridge Rule to match events from Lambda Function 1
        event_rule = events.Rule(
            self, "ScheduledEventRule",
            description="Rule to match scheduled events from Event Generator Lambda",
            event_pattern=events.EventPattern(
                source=["custom.event.generator"],
                detail_type=["Scheduled Lambda Event"]
            )
        )

        # Add Step Function as target for the EventBridge Rule
        event_rule.add_target(
            targets.SfnStateMachine(
                machine=wait_and_invoke_sfn,
                input=events.RuleTargetInput.from_object({
                    "detail": events.EventField.from_path("$.detail"),
                    "source": events.EventField.from_path("$.source"),
                    "detail-type": events.EventField.from_path("$.detail-type"),
                    "time": events.EventField.from_path("$.time")
                })
            )
        )

        # Outputs
        CfnOutput(
            self, "EventGeneratorLambdaArn",
            value=event_generator_lambda.function_arn,
            description="ARN of the Event Generator Lambda Function"
        )

        CfnOutput(
            self, "EventGeneratorLambdaName",
            value=event_generator_lambda.function_name,
            description="Name of the Event Generator Lambda Function"
        )

        CfnOutput(
            self, "TimePrinterLambdaArn",
            value=time_printer_lambda.function_arn,
            description="ARN of the Time Printer Lambda Function"
        )

        CfnOutput(
            self, "StepFunctionArn",
            value=wait_and_invoke_sfn.state_machine_arn,
            description="ARN of the Step Function State Machine"
        )

        CfnOutput(
            self, "EventRuleArn",
            value=event_rule.rule_arn,
            description="ARN of the EventBridge Rule"
        )

        CfnOutput(
            self, "StepFunctionLogGroupName",
            value=step_function_log_group.log_group_name,
            description="CloudWatch Log Group for Step Function execution logs"
        )

        # Create SNS Topic for Alerts
        alert_topic = sns.Topic(
            self, "StepFunctionAlertTopic",
            topic_name="step-function-alerts",
            display_name="Step Function Monitoring Alerts"
        )

        # CloudWatch Dashboard for Express Step Functions
        dashboard = cloudwatch.Dashboard(
            self, "StepFunctionMonitoringDashboard",
            dashboard_name="EventBridge-StepFunction-Lambda-Dashboard",
            widgets=[
                [
                    # Step Function Execution Metrics
                    cloudwatch.GraphWidget(
                        title="Step Function Executions",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/States",
                                metric_name="ExecutionsStarted",
                                dimensions_map={
                                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/States",
                                metric_name="ExecutionsSucceeded",
                                dimensions_map={
                                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/States",
                                metric_name="ExecutionsFailed",
                                dimensions_map={
                                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    # Execution Duration
                    cloudwatch.GraphWidget(
                        title="Execution Duration",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/States",
                                metric_name="ExecutionTime",
                                dimensions_map={
                                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                                },
                                statistic="Average",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    ),
                    # Lambda Function Metrics
                    cloudwatch.GraphWidget(
                        title="Lambda Function Invocations",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                dimensions_map={
                                    "FunctionName": event_generator_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Invocations",
                                dimensions_map={
                                    "FunctionName": time_printer_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    )
                ],
                [
                    # EventBridge Rule Metrics
                    cloudwatch.GraphWidget(
                        title="EventBridge Rule Matches",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Events",
                                metric_name="MatchedEvents",
                                dimensions_map={
                                    "RuleName": event_rule.rule_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/Events",
                                metric_name="SuccessfulInvocations",
                                dimensions_map={
                                    "RuleName": event_rule.rule_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    ),
                    # Lambda Errors and Duration
                    cloudwatch.GraphWidget(
                        title="Lambda Errors & Duration",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Errors",
                                dimensions_map={
                                    "FunctionName": event_generator_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Errors",
                                dimensions_map={
                                    "FunctionName": time_printer_lambda.function_name
                                },
                                statistic="Sum",
                                period=Duration.minutes(5)
                            )
                        ],
                        right=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Duration",
                                dimensions_map={
                                    "FunctionName": time_printer_lambda.function_name
                                },
                                statistic="Average",
                                period=Duration.minutes(5)
                            )
                        ],
                        width=6,
                        height=6
                    )
                ]
            ]
        )

        # CloudWatch Alarms for monitoring
        # Alarm for Step Function failures
        step_function_failure_alarm = cloudwatch.Alarm(
            self, "StepFunctionFailureAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/States",
                metric_name="ExecutionsFailed",
                dimensions_map={
                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=5,
            evaluation_periods=2,
            alarm_description="Step Function has more than 5 failures in 10 minutes",
            alarm_name="StepFunction-HighFailureRate"
        )
        
        step_function_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(alert_topic)
        )

        # Alarm for high execution volume (potential cost concern)
        high_execution_alarm = cloudwatch.Alarm(
            self, "HighExecutionVolumeAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/States",
                metric_name="ExecutionsStarted",
                dimensions_map={
                    "StateMachineArn": wait_and_invoke_sfn.state_machine_arn
                },
                statistic="Sum",
                period=Duration.minutes(15)
            ),
            threshold=1000,
            evaluation_periods=1,
            alarm_description="Step Function executions exceed 1000 in 15 minutes",
            alarm_name="StepFunction-HighExecutionVolume"
        )
        
        high_execution_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(alert_topic)
        )

        # Alarm for Lambda function errors
        lambda_error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={
                    "FunctionName": time_printer_lambda.function_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=3,
            evaluation_periods=2,
            alarm_description="Lambda function has more than 3 errors in 10 minutes",
            alarm_name="Lambda-TimePrinter-HighErrorRate"
        )
        
        lambda_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(alert_topic)
        )

        # Alarm for EventBridge rule failures
        eventbridge_failure_alarm = cloudwatch.Alarm(
            self, "EventBridgeFailureAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/Events",
                metric_name="FailedInvocations",
                dimensions_map={
                    "RuleName": event_rule.rule_name
                },
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            alarm_description="EventBridge rule has failed invocations",
            alarm_name="EventBridge-FailedInvocations",
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        eventbridge_failure_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(alert_topic)
        )

        # Create custom metrics for Express Step Functions monitoring
        # Add a metric filter for step function execution logs
        execution_started_filter = logs.MetricFilter(
            self, "ExecutionStartedFilter",
            log_group=step_function_log_group,
            metric_namespace="Custom/StepFunctions",
            metric_name="ExecutionStarted",
            filter_pattern=logs.FilterPattern.literal("[timestamp, requestId, level=\"INFO\", message=\"Execution started\", ...]"),
            metric_value="1"
        )

        execution_completed_filter = logs.MetricFilter(
            self, "ExecutionCompletedFilter",
            log_group=step_function_log_group,
            metric_namespace="Custom/StepFunctions",
            metric_name="ExecutionCompleted",
            filter_pattern=logs.FilterPattern.literal("[timestamp, requestId, level=\"INFO\", message=\"Execution completed\", ...]"),
            metric_value="1"
        )

        # Create CloudWatch Insights queries for troubleshooting
        insights_query_1 = """
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
        """

        insights_query_2 = """
fields @timestamp, @message
| filter @message like /Execution started/
| stats count() by bin(5m)
| sort @timestamp desc
        """

        insights_query_3 = """
fields @timestamp, @message
| filter @message like /Lambda invoke failed/
| sort @timestamp desc
| limit 50
        """

        # Additional outputs for monitoring resources
        CfnOutput(
            self, "AlertTopicArn",
            value=alert_topic.topic_arn,
            description="SNS Topic ARN for Step Function alerts"
        )

        CfnOutput(
            self, "DashboardName",
            value=dashboard.dashboard_name,
            description="CloudWatch Dashboard name for monitoring"
        )

        CfnOutput(
            self, "DashboardUrl",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard.dashboard_name}",
            description="CloudWatch Dashboard URL"
        )

        CfnOutput(
            self, "CloudWatchInsightsQueries",
            value="Use the following queries in CloudWatch Logs Insights:\n" +
                  "1. Error Analysis: " + insights_query_1.strip() + "\n" +
                  "2. Execution Volume: " + insights_query_2.strip() + "\n" +
                  "3. Lambda Failures: " + insights_query_3.strip(),
            description="Predefined CloudWatch Insights queries for troubleshooting"
        )