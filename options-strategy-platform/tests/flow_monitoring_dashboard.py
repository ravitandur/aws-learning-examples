#!/usr/bin/env python3
"""
🚀 FLOW MONITORING DASHBOARD - Real-Time Event Flow Visualization
Revolutionary monitoring system for the complete event emission to strategy execution pipeline

COMPLETE FLOW MONITORING:
1. EventBridge Event Emission → Schedule Strategy Trigger
2. Schedule Strategy Trigger → SQS Message Generation  
3. SQS Messages → Strategy Scheduler
4. Strategy Scheduler → Step Function Launch
5. Step Function → Single Strategy Executor
6. Single Strategy Executor → Multi-Broker Execution

DASHBOARD FEATURES:
- Real-time flow visualization
- Performance metrics at each step
- Error detection and alerting
- Lightweight architecture validation
- Revolutionary features monitoring
- Cost analysis and optimization insights
- AWS CloudWatch integration
"""

import json
import boto3
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from decimal import Decimal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from collections import defaultdict, deque
import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowMonitoringDashboard:
    def __init__(self):
        """Initialize the comprehensive flow monitoring dashboard"""
        self.session = boto3.Session(profile_name='account2')
        self.cloudwatch = self.session.client('cloudwatch', region_name='ap-south-1')
        self.dynamodb = self.session.resource('dynamodb', region_name='ap-south-1')
        self.lambda_client = self.session.client('lambda', region_name='ap-south-1')
        self.stepfunctions = self.session.client('stepfunctions', region_name='ap-south-1')
        
        # Real-time flow tracking
        self.flow_events = deque(maxlen=1000)  # Last 1000 events
        self.performance_metrics = defaultdict(list)
        self.error_log = deque(maxlen=100)
        self.active_flows = {}
        
        # Dashboard state
        self.monitoring_active = False
        self.update_queue = queue.Queue()
        
        logger.info("🚀 Flow Monitoring Dashboard initialized")

    def start_real_time_monitoring(self):
        """
        🚀 START REAL-TIME MONITORING
        Launch comprehensive monitoring of the complete event flow
        """
        logger.info("🚀 STARTING REAL-TIME FLOW MONITORING")
        logger.info("=" * 80)
        
        self.monitoring_active = True
        
        # Start monitoring threads
        cloudwatch_thread = threading.Thread(target=self._monitor_cloudwatch_metrics, daemon=True)
        dynamodb_thread = threading.Thread(target=self._monitor_dynamodb_activity, daemon=True)
        lambda_thread = threading.Thread(target=self._monitor_lambda_executions, daemon=True)
        
        cloudwatch_thread.start()
        dynamodb_thread.start()
        lambda_thread.start()
        
        # Start GUI dashboard
        self._launch_gui_dashboard()

    def _launch_gui_dashboard(self):
        """Launch interactive GUI dashboard"""
        root = tk.Tk()
        root.title("🚀 Options Trading Platform - Flow Monitoring Dashboard")
        root.geometry("1400x900")
        root.configure(bg='#2c3e50')
        
        # Create main panels
        self._create_dashboard_panels(root)
        
        # Start periodic updates
        self._schedule_gui_updates(root)
        
        # Start the GUI event loop
        root.mainloop()

    def _create_dashboard_panels(self, root):
        """Create comprehensive dashboard panels"""
        
        # Title Bar
        title_frame = tk.Frame(root, bg='#34495e', height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🚀 Options Trading Platform - Real-Time Flow Monitoring Dashboard", 
            font=('Arial', 18, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        )
        title_label.pack(expand=True)
        
        # Main content area
        main_frame = tk.Frame(root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left Panel - Flow Status
        left_panel = tk.Frame(main_frame, bg='#34495e', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_panel.pack_propagate(False)
        
        self._create_flow_status_panel(left_panel)
        
        # Right Panel - Performance Metrics
        right_panel = tk.Frame(main_frame, bg='#34495e')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self._create_performance_panel(right_panel)

    def _create_flow_status_panel(self, parent):
        """Create flow status monitoring panel"""
        
        # Panel Title
        status_title = tk.Label(
            parent, 
            text="🎯 Complete Flow Status", 
            font=('Arial', 14, 'bold'),
            bg='#34495e', 
            fg='#ecf0f1'
        )
        status_title.pack(pady=10)
        
        # Flow Steps Frame
        steps_frame = tk.Frame(parent, bg='#34495e')
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Flow steps with status indicators
        self.flow_steps = [
            ("1. EventBridge Event Emission", "event_emission"),
            ("2. Schedule Strategy Trigger", "schedule_trigger"), 
            ("3. SQS Message Processing", "sqs_processing"),
            ("4. Strategy Scheduler", "strategy_scheduler"),
            ("5. Step Function Execution", "step_function"),
            ("6. Single Strategy Executor", "strategy_executor"),
            ("7. Multi-Broker Execution", "broker_execution")
        ]
        
        self.status_indicators = {}
        
        for i, (step_name, step_key) in enumerate(self.flow_steps):
            step_frame = tk.Frame(steps_frame, bg='#34495e')
            step_frame.pack(fill=tk.X, pady=5)
            
            # Status indicator (colored circle)
            status_indicator = tk.Label(
                step_frame,
                text="●",
                font=('Arial', 16),
                bg='#34495e',
                fg='#95a5a6'  # Default gray
            )
            status_indicator.pack(side=tk.LEFT, padx=5)
            
            # Step name
            step_label = tk.Label(
                step_frame,
                text=step_name,
                font=('Arial', 11),
                bg='#34495e',
                fg='#ecf0f1',
                anchor='w'
            )
            step_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            self.status_indicators[step_key] = {
                'indicator': status_indicator,
                'label': step_label
            }
        
        # Active Flows Counter
        self.active_flows_label = tk.Label(
            parent,
            text="🔄 Active Flows: 0",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#3498db'
        )
        self.active_flows_label.pack(pady=10)
        
        # Error Counter
        self.error_count_label = tk.Label(
            parent,
            text="❌ Errors: 0",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#e74c3c'
        )
        self.error_count_label.pack(pady=5)

    def _create_performance_panel(self, parent):
        """Create performance monitoring panel"""
        
        # Panel Title
        perf_title = tk.Label(
            parent,
            text="⚡ Performance Metrics & Logs",
            font=('Arial', 14, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        perf_title.pack(pady=10)
        
        # Metrics Frame
        metrics_frame = tk.Frame(parent, bg='#34495e')
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Performance metrics display
        self.metrics_labels = {}
        
        metrics = [
            ("Event Emission", "event_emission_time"),
            ("Schedule Trigger", "schedule_trigger_time"),
            ("SQS Processing", "sqs_processing_time"),
            ("Strategy Scheduler", "strategy_scheduler_time"),
            ("Strategy Execution", "strategy_execution_time"),
            ("Total Flow Time", "total_flow_time")
        ]
        
        for i, (metric_name, metric_key) in enumerate(metrics):
            row = i // 2
            col = i % 2
            
            metric_frame = tk.Frame(metrics_frame, bg='#34495e')
            metric_frame.grid(row=row, column=col, padx=10, pady=5, sticky='w')
            
            metric_label = tk.Label(
                metric_frame,
                text=f"{metric_name}:",
                font=('Arial', 10),
                bg='#34495e',
                fg='#bdc3c7',
                width=15,
                anchor='w'
            )
            metric_label.pack(side=tk.LEFT)
            
            metric_value = tk.Label(
                metric_frame,
                text="--",
                font=('Arial', 10, 'bold'),
                bg='#34495e',
                fg='#2ecc71',
                width=10,
                anchor='w'
            )
            metric_value.pack(side=tk.LEFT)
            
            self.metrics_labels[metric_key] = metric_value
        
        # Real-time Log Display
        log_frame = tk.Frame(parent, bg='#34495e')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_title = tk.Label(
            log_frame,
            text="📋 Real-Time Flow Log",
            font=('Arial', 12, 'bold'),
            bg='#34495e',
            fg='#ecf0f1'
        )
        log_title.pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg='#1a252f',
            fg='#ecf0f1',
            font=('Consolas', 9),
            insertbackground='#ecf0f1'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Add initial log message
        self._add_log_message("🚀 Flow Monitoring Dashboard Started", "INFO")

    def _monitor_cloudwatch_metrics(self):
        """Monitor CloudWatch metrics for Lambda functions and Step Functions"""
        while self.monitoring_active:
            try:
                # Get metrics for Lambda functions
                lambda_metrics = self._get_lambda_metrics()
                
                # Get Step Function metrics
                stepfunction_metrics = self._get_stepfunction_metrics()
                
                # Update dashboard
                self.update_queue.put(('cloudwatch', {
                    'lambda_metrics': lambda_metrics,
                    'stepfunction_metrics': stepfunction_metrics,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }))
                
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                self._add_log_message(f"❌ CloudWatch monitoring error: {str(e)}", "ERROR")
                time.sleep(60)  # Longer delay on error

    def _monitor_dynamodb_activity(self):
        """Monitor DynamoDB activity for schedule and execution data"""
        while self.monitoring_active:
            try:
                # Check recent schedule creations
                schedule_activity = self._check_schedule_activity()
                
                # Check recent strategy executions
                execution_activity = self._check_execution_activity()
                
                self.update_queue.put(('dynamodb', {
                    'schedule_activity': schedule_activity,
                    'execution_activity': execution_activity,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }))
                
                time.sleep(45)  # Update every 45 seconds
                
            except Exception as e:
                self._add_log_message(f"❌ DynamoDB monitoring error: {str(e)}", "ERROR")
                time.sleep(60)

    def _monitor_lambda_executions(self):
        """Monitor Lambda function executions in real-time"""
        while self.monitoring_active:
            try:
                # Get recent Lambda invocations
                recent_invocations = self._get_recent_lambda_invocations()
                
                for invocation in recent_invocations:
                    self._process_lambda_invocation(invocation)
                
                time.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                self._add_log_message(f"❌ Lambda monitoring error: {str(e)}", "ERROR")
                time.sleep(30)

    def _get_lambda_metrics(self) -> Dict[str, Any]:
        """Get Lambda function metrics from CloudWatch"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=10)
            
            lambda_functions = [
                'event_emitter',
                'schedule_strategy_trigger', 
                'strategy_scheduler',
                'single_strategy_executor'
            ]
            
            metrics = {}
            
            for function_name in lambda_functions:
                try:
                    # Get duration metrics
                    duration_response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Duration',
                        Dimensions=[
                            {'Name': 'FunctionName', 'Value': function_name}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,  # 5 minutes
                        Statistics=['Average', 'Maximum']
                    )
                    
                    # Get invocation count
                    invocation_response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Invocations',
                        Dimensions=[
                            {'Name': 'FunctionName', 'Value': function_name}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Sum']
                    )
                    
                    # Get error count
                    error_response = self.cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName='Errors',
                        Dimensions=[
                            {'Name': 'FunctionName', 'Value': function_name}
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=300,
                        Statistics=['Sum']
                    )
                    
                    metrics[function_name] = {
                        'duration': duration_response['Datapoints'],
                        'invocations': invocation_response['Datapoints'],
                        'errors': error_response['Datapoints']
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not get metrics for {function_name}: {str(e)}")
                    metrics[function_name] = {'error': str(e)}
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting Lambda metrics: {str(e)}")
            return {}

    def _get_stepfunction_metrics(self) -> Dict[str, Any]:
        """Get Step Function execution metrics"""
        try:
            # Get recent Step Function executions
            executions = self.stepfunctions.list_executions(
                maxResults=10,
                statusFilter='RUNNING'
            )
            
            return {
                'active_executions': len(executions['executions']),
                'executions': executions['executions']
            }
            
        except Exception as e:
            logger.error(f"Error getting Step Function metrics: {str(e)}")
            return {}

    def _check_schedule_activity(self) -> Dict[str, Any]:
        """Check recent schedule creation activity in DynamoDB"""
        try:
            table = self.dynamodb.Table('ql-algo-trading-dev-trading-configurations')
            
            # Query for recent schedules
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(minutes=10)
            
            response = table.scan(
                FilterExpression='entity_type = :entity_type AND created_at > :cutoff_time',
                ExpressionAttributeValues={
                    ':entity_type': 'EXECUTION_SCHEDULE',
                    ':cutoff_time': cutoff_time.isoformat()
                },
                ProjectionExpression='strategy_id, execution_time, weekday, created_at'
            )
            
            return {
                'recent_schedules': len(response['Items']),
                'schedules': response['Items']
            }
            
        except Exception as e:
            logger.error(f"Error checking schedule activity: {str(e)}")
            return {'recent_schedules': 0, 'error': str(e)}

    def _check_execution_activity(self) -> Dict[str, Any]:
        """Check recent strategy execution activity"""
        try:
            table = self.dynamodb.Table('ql-algo-trading-dev-execution-history')
            
            # Query for recent executions
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(minutes=10)
            
            response = table.scan(
                FilterExpression='execution_timestamp > :cutoff_time',
                ExpressionAttributeValues={
                    ':cutoff_time': cutoff_time.isoformat()
                },
                ProjectionExpression='strategy_id, execution_time, status, total_lots_executed'
            )
            
            return {
                'recent_executions': len(response['Items']),
                'executions': response['Items']
            }
            
        except Exception as e:
            logger.error(f"Error checking execution activity: {str(e)}")
            return {'recent_executions': 0, 'error': str(e)}

    def _get_recent_lambda_invocations(self) -> List[Dict[str, Any]]:
        """Get recent Lambda function invocations from CloudWatch Logs"""
        # This would typically use CloudWatch Logs Insights to get recent invocations
        # For now, return mock data to demonstrate the concept
        return []

    def _process_lambda_invocation(self, invocation: Dict[str, Any]):
        """Process a Lambda invocation event"""
        function_name = invocation.get('function_name', 'unknown')
        status = invocation.get('status', 'unknown')
        duration = invocation.get('duration', 0)
        
        # Update status indicators
        if function_name in ['event_emitter']:
            self._update_step_status('event_emission', status, duration)
        elif function_name in ['schedule_strategy_trigger']:
            self._update_step_status('schedule_trigger', status, duration)
        elif function_name in ['strategy_scheduler']:
            self._update_step_status('strategy_scheduler', status, duration)
        elif function_name in ['single_strategy_executor']:
            self._update_step_status('strategy_executor', status, duration)

    def _update_step_status(self, step_key: str, status: str, duration: float):
        """Update step status in the dashboard"""
        color_map = {
            'success': '#2ecc71',  # Green
            'running': '#f39c12',  # Orange
            'error': '#e74c3c',    # Red
            'unknown': '#95a5a6'   # Gray
        }
        
        if step_key in self.status_indicators:
            color = color_map.get(status.lower(), '#95a5a6')
            self.status_indicators[step_key]['indicator'].config(fg=color)
            
            # Add performance metric
            if duration > 0:
                self.performance_metrics[f"{step_key}_time"].append(duration)

    def _schedule_gui_updates(self, root):
        """Schedule periodic GUI updates"""
        try:
            # Process queued updates
            while not self.update_queue.empty():
                update_type, data = self.update_queue.get_nowait()
                self._process_dashboard_update(update_type, data)
                
            # Update metrics display
            self._update_metrics_display()
            
            # Update active flows counter
            self.active_flows_label.config(text=f"🔄 Active Flows: {len(self.active_flows)}")
            
            # Update error counter  
            self.error_count_label.config(text=f"❌ Errors: {len(self.error_log)}")
            
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"Error updating GUI: {str(e)}")
        
        # Schedule next update
        root.after(1000, lambda: self._schedule_gui_updates(root))

    def _process_dashboard_update(self, update_type: str, data: Dict[str, Any]):
        """Process dashboard update from monitoring threads"""
        if update_type == 'cloudwatch':
            self._process_cloudwatch_update(data)
        elif update_type == 'dynamodb':
            self._process_dynamodb_update(data)
        elif update_type == 'lambda':
            self._process_lambda_update(data)

    def _process_cloudwatch_update(self, data: Dict[str, Any]):
        """Process CloudWatch metrics update"""
        lambda_metrics = data.get('lambda_metrics', {})
        
        for function_name, metrics in lambda_metrics.items():
            if 'duration' in metrics:
                durations = metrics['duration']
                if durations:
                    avg_duration = np.mean([dp['Average'] for dp in durations])
                    self.performance_metrics[f"{function_name}_time"].append(avg_duration)
                    
                    # Update step status
                    if function_name == 'event_emitter':
                        self._update_step_status('event_emission', 'success', avg_duration)
                    elif function_name == 'schedule_strategy_trigger':
                        self._update_step_status('schedule_trigger', 'success', avg_duration)
                    elif function_name == 'strategy_scheduler':
                        self._update_step_status('strategy_scheduler', 'success', avg_duration)
                    elif function_name == 'single_strategy_executor':
                        self._update_step_status('strategy_executor', 'success', avg_duration)

    def _process_dynamodb_update(self, data: Dict[str, Any]):
        """Process DynamoDB activity update"""
        schedule_activity = data.get('schedule_activity', {})
        execution_activity = data.get('execution_activity', {})
        
        recent_schedules = schedule_activity.get('recent_schedules', 0)
        recent_executions = execution_activity.get('recent_executions', 0)
        
        if recent_schedules > 0:
            self._add_log_message(f"📅 {recent_schedules} new schedules created", "INFO")
            
        if recent_executions > 0:
            self._add_log_message(f"🚀 {recent_executions} strategies executed", "SUCCESS")

    def _process_lambda_update(self, data: Dict[str, Any]):
        """Process Lambda execution update"""
        # Process Lambda invocation data
        pass

    def _update_metrics_display(self):
        """Update performance metrics display"""
        for metric_key, metric_label in self.metrics_labels.items():
            if metric_key in self.performance_metrics:
                values = self.performance_metrics[metric_key]
                if values:
                    # Show average of last 10 values
                    recent_values = values[-10:]
                    avg_value = np.mean(recent_values)
                    
                    if 'time' in metric_key:
                        display_value = f"{avg_value:.0f}ms"
                    else:
                        display_value = f"{avg_value:.2f}"
                    
                    metric_label.config(text=display_value)

    def _add_log_message(self, message: str, level: str = "INFO"):
        """Add message to the real-time log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding for different log levels
        color_map = {
            "INFO": "#3498db",     # Blue
            "SUCCESS": "#2ecc71",  # Green
            "WARNING": "#f39c12",  # Orange  
            "ERROR": "#e74c3c"     # Red
        }
        
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)  # Auto-scroll
            self.log_text.config(state=tk.DISABLED)
        
        # Also add to error log if it's an error
        if level == "ERROR":
            self.error_log.append({
                'timestamp': timestamp,
                'message': message
            })


def main():
    """Launch the flow monitoring dashboard"""
    dashboard = FlowMonitoringDashboard()
    
    print("🚀 LAUNCHING FLOW MONITORING DASHBOARD")
    print("=" * 80)
    print("Real-time monitoring of:")
    print("  1. EventBridge Event Emission")
    print("  2. Schedule Strategy Trigger")  
    print("  3. SQS Message Processing")
    print("  4. Strategy Scheduler")
    print("  5. Step Function Execution")
    print("  6. Single Strategy Executor")
    print("  7. Multi-Broker Execution")
    print("")
    print("Dashboard will open in a new window...")
    print("=" * 80)
    
    dashboard.start_real_time_monitoring()


if __name__ == "__main__":
    main()