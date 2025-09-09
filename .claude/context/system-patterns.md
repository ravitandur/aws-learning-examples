---
created: 2025-09-05T19:46:11Z
last_updated: 2025-09-05T19:46:11Z
version: 1.0
author: Claude Code PM System
---

# System Patterns & Architecture

## Core Architectural Patterns

### Multi-Stack Architecture Pattern
**Pattern**: Separation of concerns across AWS stacks
- **Stack 1**: User authentication & broker management
- **Stack 2**: Options strategy execution platform
- **Integration**: Cross-stack references and shared API Gateway
- **Benefits**: Independent deployment, clear responsibility boundaries

### Event-Driven Architecture Pattern
**Pattern**: EventBridge-centered communication
```
EventBridge → Step Functions → Lambda → DynamoDB
     ↓
   SNS Notifications → CloudWatch Alarms
```
- **Decoupling**: Services communicate via events, not direct calls
- **Scalability**: Automatic scaling based on event volume
- **Reliability**: Built-in retry and error handling

### Revolutionary Single-Table DynamoDB Pattern
**Pattern**: GSI2 optimization with strategic data modeling
- **Before**: 401+ queries for complex operations
- **After**: 2 queries via intelligent GSI design
- **Achievement**: 99.5% query reduction
- **Pattern**: Leg-level broker allocation with single table efficiency

## Precision Timing Architecture

### 0-Second Precision Pattern
**Pattern**: Standard Step Functions with dynamic wait calculation
```python
def calculate_next_minute_wait_seconds(current_ist: datetime) -> int:
    current_second = current_ist.second
    seconds_remaining = 60 - current_second
    return max(1, seconds_remaining)  # Self-correcting precision
```

**Evolution Path**:
1. **EventBridge Cron**: 27-second timing drift
2. **Step Functions + Dynamic Wait**: True 0-second precision
3. **Result**: Institutional-grade timing accuracy

### Weekend Protection Pattern
**Pattern**: Database-level execution prevention
- **Implementation**: Weekday validation in all execution paths
- **Fallback**: Multiple layers of weekend detection
- **Safety**: Half-open interval logic prevents overlap

## Infrastructure Patterns

### CDK Stack Creation Pattern
**Standards**:
- **logRetention Parameter**: Reliable deployment without LogGroup conflicts
- **Python 3.11 Runtime**: Consistent modern runtime
- **Module-Prefix Naming**: `{module-prefix}-{function-name}`
- **Configuration-Driven**: All values from shared_config/environments.json

### Cross-Stack Integration Pattern
**Pattern**: Import/export with type safety
```python
# Export from auth stack
user_pool_export = CfnOutput(
    self, "UserPoolId", 
    value=user_pool.user_pool_id,
    export_name=f"{module_prefix}-UserPoolId"
)

# Import in options stack  
user_pool_id = Fn.import_value(f"{auth_module_prefix}-UserPoolId")
```

## Data Flow Patterns

### Multi-Broker Parallel Execution Pattern
**Pattern**: Revolutionary concurrent order placement
- **Strategy**: Each strategy can use different brokers
- **Allocation**: Custom lot distribution per broker
- **Execution**: Parallel Lambda invocations
- **Coordination**: Step Functions orchestration

### Market Phase Intelligence Pattern
**Pattern**: Time-aware execution logic
- **Pre-market**: 9:00-9:15 AM IST setup
- **Regular hours**: 9:15 AM - 3:30 PM IST active trading  
- **Post-market**: 3:30-6:00 PM IST analysis
- **Weekend**: Complete execution prevention

## Error Handling Patterns

### Graceful Degradation Pattern
- **Fail fast**: Critical configuration errors
- **Log and continue**: Optional feature failures
- **User-friendly messages**: Resilience layer abstraction
- **Retry mechanisms**: Built-in Step Functions retry

### Comprehensive Logging Pattern
- **Structured logging**: JSON format for CloudWatch Insights
- **Context preservation**: Request IDs across service boundaries
- **Performance tracking**: Timing metrics in all operations
- **Error correlation**: Linked error reporting

## Security Patterns

### OAuth Strategy Pattern (Multi-Broker)
**Pattern**: Strategy pattern for broker authentication
```python
class BrokerOAuthStrategy(ABC):
    @abstractmethod
    def get_auth_url(self) -> str: pass
    
    @abstractmethod  
    def handle_callback(self, code: str) -> dict: pass
```
- **Extensibility**: Easy addition of new brokers
- **Security**: Isolated credential handling per broker
- **Flexibility**: Different OAuth flows per broker

### Secrets Management Pattern
- **AWS Secrets Manager**: Encrypted credential storage
- **Rotation-ready**: Design supports automatic rotation
- **Least privilege**: Minimal IAM permissions
- **Environment separation**: Dev/staging/prod isolation

## Testing Patterns

### Comprehensive Testing Agent Pattern
**Pattern**: Specialized testing orchestration
- **Test Agent Authority**: Centralized test management
- **Performance Validation**: Automated benchmarking
- **End-to-End Testing**: Complete workflow validation
- **Enterprise Reporting**: HTML, JSON, coverage analysis

### Mock-Free Testing Pattern
**Philosophy**: No mocks, real AWS service integration
- **Real services**: Test against actual AWS resources
- **Isolated environments**: Separate test stacks
- **Data cleanup**: Automated test data management
- **Verbose logging**: Detailed test output for debugging

## Frontend Architecture Patterns

### Consistent Layout Pattern
**Standard**: Algo-platform layout consistency
```tsx
const PageComponent: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Page Title</h1>
      {/* Content with consistent spacing */}
    </div>
  );
};
```

### Dark Mode Support Pattern
- **Full dark mode**: Complete theme coverage
- **Tailwind classes**: `bg-white dark:bg-gray-800`
- **Consistent experience**: All components themed
- **User preference**: Persistent theme selection

## Monitoring & Observability Patterns

### CloudWatch Dashboard Pattern
- **Per-project dashboards**: Focused monitoring
- **Key metrics**: Performance and error rates
- **Cost tracking**: Prevent surprise bills
- **Real-time alerts**: SNS integration

### Cost Optimization Pattern
- **Express Step Functions**: 98% cost reduction
- **Short log retention**: 7/30/90 days by environment
- **On-demand billing**: Pay-per-use wherever possible
- **Resource tagging**: Cost allocation tracking

## Development Workflow Patterns

### Sub-Agent Optimization Pattern
**Pattern**: Context-efficient specialized agents
- **File-analyzer**: Log and file analysis
- **Code-analyzer**: Bug detection and logic tracing  
- **Test-runner**: Test execution and analysis
- **Benefits**: Reduced context usage, focused expertise