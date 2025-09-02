# Options Strategy Platform - CLAUDE.md

This file provides guidance to Claude Code when working with the Options Strategy Platform module.

## Project Overview

**Module**: Options Strategy Platform (Parallel to user-auth-broker-management)  
**Purpose**: Complete options trading platform with strategy management, execution engine, and real-time analytics  
**Stack Name**: `ql-algo-trading-{env}-options-trading-stack`  
**Dependencies**: user-auth-broker-management stack (for user authentication and broker accounts)

## Project Structure

This is a **parallel project** that integrates with the existing user-auth-broker-management stack:

```
options-strategy-platform/
├── app.py                          # CDK application entry point
├── cdk_stack/
│   └── options_trading_stack.py    # Comprehensive options trading stack
├── lambda_functions/
│   └── option_baskets/             # All Lambda functions for options platform
│       ├── basket_manager.py       # Basket CRUD operations
│       ├── strategy_manager.py     # Strategy management
│       ├── strategy_broker_allocator.py  # KEY INNOVATION: Strategy-specific broker allocation
│       └── [other functions...]
├── config/                         # Project-specific configuration (if needed)
├── requirements.txt                # Options-specific Python dependencies
├── venv/                          # Isolated virtual environment
├── deploy.sh -> ../shared_scripts/deploy.sh   # Symlink to shared deployment
└── CLAUDE.md                      # This file
```

## Key Innovations

### 1. Strategy-Specific Broker Allocation (Revolutionary Feature)
This platform's **core innovation** allows each strategy within a basket to have different broker configurations:

**Example Use Case:**
- **Basket**: "Conservative Income Strategies"  
  - **Strategy A** (Iron Condor): 2 lots on Zerodha + 1 lot on Angel One
  - **Strategy B** (Covered Call): 5 lots only on Zerodha  
  - **Strategy C** (Cash Secured Put): 3 lots on Finvasia + 2 lots on Angel One

**Benefits:**
- Maximum flexibility for risk distribution
- Optimal broker utilization per strategy type
- Independent risk limits per strategy-broker combination
- Dynamic lot allocation based on strategy performance

### 2. Unified Admin Marketplace
- **Admin-Created Baskets**: Professional strategies available for subscription
- **User Subscriptions**: Subscribe to admin strategies with custom broker allocations
- **Revenue Model**: Performance-based fees and subscription management

### 3. Complete Options Trading Engine
- Multi-leg strategy support (Iron Condors, Straddles, Strangles, etc.)
- Real-time market data integration
- Advanced Greeks calculations
- Risk management and position tracking

## Database Design

### Core Tables (9 Total)
1. **options-baskets**: Unified basket storage (user & admin baskets)
2. **options-strategies**: Strategy configurations with legs
3. **strategy-broker-allocations**: **KEY TABLE** - Strategy-specific broker configurations
4. **basket-subscriptions**: Marketplace subscription management
5. **strategy-executions**: Execution tracking and history
6. **order-history**: Multi-broker order management
7. **position-tracker**: Real-time position monitoring
8. **performance-metrics**: Analytics and performance data
9. **market-data-cache**: Real-time market data with TTL

### Cross-Stack Integration
- **Imports from Stack 1**: User Pool ID, Broker Accounts Table, API Gateway
- **Data Flow**: User authentication → Broker accounts → Strategy allocation → Execution

## API Endpoints

### Strategy-Broker Allocation (Core Innovation)
```yaml
GET    /options/strategies/{strategy_id}/brokers           # List broker allocations
POST   /options/strategies/{strategy_id}/brokers           # Create broker allocation  
PUT    /options/strategies/{strategy_id}/brokers/{id}      # Update allocation
DELETE /options/strategies/{strategy_id}/brokers/{id}      # Remove allocation
```

### Basket Management
```yaml
GET    /options/baskets                    # My baskets + marketplace browsing
POST   /options/baskets                    # Create new basket
GET    /options/baskets/{basket_id}        # Basket details with strategies
PUT    /options/baskets/{basket_id}        # Update basket
DELETE /options/baskets/{basket_id}        # Delete basket
```

### Strategy Management
```yaml
GET    /options/strategies                          # My strategies across baskets
POST   /options/baskets/{basket_id}/strategies     # Create strategy in basket
GET    /options/strategies/{strategy_id}           # Strategy details with legs
PUT    /options/strategies/{strategy_id}           # Update strategy
DELETE /options/strategies/{strategy_id}           # Delete strategy
```

## Deployment Commands

### Development Deployment
```bash
# Deploy options trading stack
./deploy.sh -p options-strategy-platform -e dev -a account2

# Deploy with specific environment
./shared_scripts/deploy.sh -p options-strategy-platform -e staging -a account2
```

### Deployment Sequence
1. **Ensure Stack 1 is deployed**: user-auth-broker-management must be deployed first
2. **Deploy options platform**: This stack imports outputs from Stack 1
3. **Verify integration**: Test cross-stack API calls and data flow

### Stack Dependencies
```yaml
Dependencies:
  - user-auth-broker-management (Stack 1) MUST be deployed first
  - Imports: UserPoolId, BrokerAccountsTable, ApiGatewayId from Stack 1
  - Shares: Same Cognito user pool, same API Gateway (extended)
```

## Configuration

### Shared Configuration Usage
This project uses the shared configuration at `/shared_config/environments.json`:

```json
{
  "projects": {
    "options_trading": {
      "config": {
        "market_data_ttl_seconds": 300,
        "enable_realtime_websocket": true,
        "max_strategies_per_basket": 10,
        "max_legs_per_strategy": 6,
        "execution_timeout_seconds": 30,
        "enable_paper_trading": true,
        "indian_market_config": {
          "trading_start_time": "09:15",
          "trading_end_time": "15:30",
          "indices": {
            "NIFTY": {"lot_size": 25, "weekly_expiry": "THURSDAY"},
            "BANKNIFTY": {"lot_size": 15, "weekly_expiry": "WEDNESDAY"}
          }
        }
      }
    }
  }
}
```

## Indian Market Specialization

### Supported Indices
- **NIFTY**: 25 lot size, Thursday expiry
- **BANKNIFTY**: 15 lot size, Wednesday expiry  
- **FINNIFTY**: 25 lot size, Tuesday expiry
- **MIDCPNIFTY**: 75 lot size, Monday expiry
- **SENSEX**: 10 lot size, Friday expiry

### Market Hours Integration
- **Trading Session**: 09:15 - 15:30 IST
- **Holiday Calendar**: Indian market holidays
- **Expiry Management**: Automatic expiry date calculation

## Development Workflow

### Adding New Features
1. **Lambda Functions**: Add to `lambda_functions/option_baskets/`
2. **API Endpoints**: Update `options_trading_stack.py`
3. **Database Tables**: Add to stack with proper GSIs
4. **Shared Utilities**: Use `shared_utils/` (automatically copied)

### Testing Strategy
1. **Unit Tests**: Test individual Lambda functions
2. **Integration Tests**: Test cross-stack communication
3. **End-to-End**: Test complete workflow (basket → strategy → allocation → execution)

### Key Files to Understand
- `basket_manager.py`: Core basket operations
- `strategy_broker_allocator.py`: **Most important** - Strategy-specific broker allocation
- `options_trading_stack.py`: Complete infrastructure definition
- `shared_utils/indian_market_utils.py`: Indian market calculations
- `shared_utils/risk_calculations.py`: Options risk management

## Architecture Principles

### 1. No Code Duplication
- Reuses `shared_utils/` across all Lambda functions
- Uses shared deployment scripts
- Leverages shared configuration files

### 2. Cross-Stack Integration
- Imports necessary resources from user-auth stack
- Extends existing API Gateway
- Shares authentication infrastructure

### 3. Indian Market Optimization  
- Native support for Indian indices and market hours
- Proper expiry date handling
- Risk calculations optimized for Indian options

### 4. Strategy-Centric Design
- Everything revolves around strategies having independent broker configurations
- Flexible lot allocation per strategy per broker
- Independent risk management per allocation

## Success Metrics

### Technical KPIs
- **Strategy Creation**: < 30 seconds for complex multi-leg strategies
- **Broker Allocation**: 100% accuracy in lot distribution across brokers
- **Real-time Updates**: < 100ms latency for position updates
- **Cross-Stack Integration**: 100% success rate for auth and broker data access

### Business KPIs
- **User Adoption**: 80% of existing users create options strategies
- **Strategy Diversity**: Average 2.5 strategies per user
- **Broker Distribution**: Users utilize multiple brokers effectively
- **Marketplace Engagement**: 60% subscription rate to admin baskets

This platform represents a **revolutionary approach to options strategy management** with its strategy-specific broker allocation system, setting it apart from all existing trading platforms.

## Latest Enterprise Standards & CDK Compliance (September 2, 2025)

### ✅ Critical LogGroup Pattern Fix - Deployment Reliability Resolved
**Major Achievement**: Fixed "LogGroup already exists" errors that prevented reliable stack redeployments

#### **Problem Identified**:
- **Issue**: Explicit LogGroup creation with `log_group` parameter caused deployment failures
- **Error**: "LogGroup already exists" on stack redeploy, especially in staging/production
- **Root Cause**: CDK doesn't handle LogGroup deletion/recreation reliably with removal policies

#### **Solution Implemented**:
1. **Reverted to logRetention Pattern**:
   - **Removed**: All 16 explicit LogGroup constructs from CDK stack
   - **Updated**: All Lambda functions to use `log_retention` parameter instead
   - **Benefit**: CDK handles LogGroup management via Custom Resources automatically

2. **Deployment Pattern Fixed**:
   - **Before**: Explicit LogGroup creation → `log_group=log_group_variable`
   - **After**: Simple `log_retention=logs.RetentionDays.ONE_WEEK` parameter
   - **Result**: `Custom::LogRetention` resources handle LogGroup lifecycle properly

3. **Environment-Specific Retention**:
   ```python
   log_retention=logs.RetentionDays.ONE_WEEK if self.env_config['log_retention_days'] == 7 
                else logs.RetentionDays.ONE_MONTH if self.env_config['log_retention_days'] == 30 
                else logs.RetentionDays.THREE_MONTHS
   ```

#### **CDK Agent Pattern Updated**:
- **Updated CDK Stack Creation Agent** to recommend `logRetention` over explicit LogGroups
- **Reasoning**: Prevents redeploy errors while maintaining same functionality
- **Trade-off**: Shows deprecation warning but ensures reliable deployments

#### **Deployment Success Metrics**:
- ✅ **Dev Environment**: Clean destroy/redeploy capability verified
- ✅ **Staging/Production**: No more manual LogGroup cleanup required
- ✅ **Log Retention**: Environment-specific retention (7/30/90 days) maintained
- ✅ **Cross-Stack Integration**: Successfully imports from auth-broker stack

### ✅ Current Deployment Status (September 2, 2025)
**Stack**: `ql-algo-trading-dev-options-trading-stack`
**API Gateway**: `https://2f8bmi4edb.execute-api.ap-south-1.amazonaws.com/dev/`
**Deployment Method**: Shared deployment script with logRetention pattern
**Cross-Stack Dependencies**: Successfully importing UserPoolId and BrokerAccountsTable from auth stack

#### **Infrastructure Summary**:
- **16 Lambda Functions**: All using Python 3.11 with logRetention pattern
- **9 DynamoDB Tables**: Complete options trading platform database
- **Cross-Stack Integration**: Imports user authentication and broker data
- **API Gateway**: Environment-specific stages with CORS
- **Custom LogRetention**: Automatic LogGroup management via CDK
- **Shared Utils Integration**: All Lambda functions have shared utilities

#### **Revolutionary Features Deployed**:
1. **Strategy-Specific Broker Allocation**: Each strategy can use different brokers with custom lot distributions
2. **9-Table Database Architecture**: Complete options trading platform with execution engine
3. **Admin Marketplace**: Professional strategies available for user subscription
4. **Multi-Leg Strategy Support**: Iron Condors, Straddles, Strangles with real-time Greeks
5. **Indian Market Integration**: Native support for NIFTY, BANKNIFTY with proper expiry handling

#### **Enterprise Standards Achieved**:
- **Reliable Redeployment**: No LogGroup conflicts on stack destroy/redeploy
- **Runtime Standardization**: All Lambda functions use Python 3.11
- **Module Prefix Naming**: Consistent `options-*` resource naming
- **Cross-Stack Architecture**: Seamless integration with user-auth-broker-management
- **Environment Configuration**: All values from shared environments.json

### ✅ Semantic Architecture Enhancement
**Revolutionary Platform Identity**: The `option_baskets` directory structure reinforces the platform's core innovation:

1. **Strategy Basket Focus**: Emphasizes the basket-centric approach to options management
2. **Multi-Strategy Containers**: Highlights that baskets contain multiple independent strategies
3. **Broker Allocation Clarity**: Better represents strategy-specific broker allocation within baskets
4. **User Mental Model**: Aligns with how traders think about organizing multiple strategies
5. **Marketplace Positioning**: Supports admin-created baskets and user subscriptions

This enhancement strengthens the platform's revolutionary approach to options strategy management with strategy-specific broker allocation, setting it apart from all existing trading platforms.