---
created: 2025-09-05T19:46:11Z
last_updated: 2025-09-11T11:38:29Z
version: 1.4
author: Claude Code PM System
---

# Project Style Guide

## Development Philosophy

### Core Principle
> **Think carefully and implement the most concise solution that changes as little code as possible.**

### Absolute Development Rules

#### Quality Standards
- **NO PARTIAL IMPLEMENTATION**: Complete features fully or don't implement
- **NO SIMPLIFICATION**: No "TODO" or "simplified for now" comments
- **NO CODE DUPLICATION**: Check existing codebase for reusable functions
- **NO DEAD CODE**: Either use code or delete it completely
- **IMPLEMENT TESTS FOR EVERY FUNCTION**: Comprehensive test coverage required
- **NO CHEATER TESTS**: Tests must be accurate and designed to reveal flaws

#### Design Standards  
- **NO INCONSISTENT NAMING**: Follow existing codebase naming patterns
- **NO OVER-ENGINEERING**: Simple functions over unnecessary abstractions
- **NO MIXED CONCERNS**: Proper separation of validation, business logic, and data
- **NO RESOURCE LEAKS**: Always close connections, clear timeouts, cleanup handles

## Code Style Conventions

### Python Style (Lambda Functions & CDK)

#### Naming Conventions
```python
# Functions: snake_case
def calculate_next_minute_wait_seconds(current_ist: datetime) -> int:

# Classes: PascalCase
class BrokerOAuthStrategy:

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3

# Variables: snake_case
current_broker_allocation = get_broker_allocation()
```

#### Function Structure
```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """
    Clear docstring explaining function purpose.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
    """
    # Implementation with clear logic flow
    pass
```

#### Error Handling Pattern
```python
try:
    # Primary operation
    result = perform_operation()
    return result
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### TypeScript/React Style (Frontend)

#### Component Structure
```tsx
interface ComponentProps {
  title: string;
  isVisible: boolean;
  onAction: () => void;
}

const ComponentName: React.FC<ComponentProps> = ({ 
  title, 
  isVisible, 
  onAction 
}) => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{title}</h1>
      {/* Component content */}
    </div>
  );
};

export default ComponentName;
```

#### Layout Patterns (Required)
```tsx
// Standard page layout - MUST follow this pattern
const PageComponent: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Page Title</h1>
      
      {/* Content sections with consistent spacing */}
      <div className="grid gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          {/* Section content */}
        </div>
      </div>
    </div>
  );
};
```

#### CSS Class Standards
```tsx
// Required patterns
<div className="space-y-6">           // Root container spacing
<h1 className="text-2xl font-bold">   // Page titles (never text-3xl)
<div className="bg-white dark:bg-gray-800 rounded-lg shadow"> // Cards
<input className="bg-white dark:bg-gray-700"> // Form inputs
```

#### 2025 Minimalist Design Standards (ENFORCED)
```tsx
// STRICT DESIGN COMPLIANCE - ALL COMPONENTS MUST FOLLOW
// 1. NO EMOJI DECORATIONS - Content-first professional interface
❌ <h1>🚀 Revolutionary Strategy Creator</h1>
✅ <h1>Strategy Creator</h1>

// 2. NO MARKETING LANGUAGE - Business-focused terminology  
❌ "Revolutionary Features Active"
✅ "Active Features"

// 3. GLASSMORPHISM EFFECTS - Modern depth with backdrop-blur
<header className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-md">

// 4. CLEAN TYPOGRAPHY - Professional, readable text hierarchy
<h1 className="text-2xl font-bold">           // Page titles only
<h2 className="text-lg font-semibold">        // Section headers
<p className="text-gray-600 dark:text-gray-300"> // Body text

// 5. SUBTLE INTERACTIONS - Hover effects over constant animations
className="hover:shadow-lg transition-all duration-200"

// 6. ICON USAGE - Functional icons, not decorative symbols
✅ <Edit className="h-4 w-4" />              // Action icons
❌ <div className="text-3xl">🎯</div>         // Decorative emojis

// 7. COLOR PSYCHOLOGY - Professional blue primary palette
text-blue-600    // Primary actions and accents
text-gray-600    // Secondary text and descriptions  
text-green-600   // Success states and positive actions
text-red-600     // Errors and destructive actions

// 8. TOAST NOTIFICATIONS - Container-managed positioning system
<ToastProvider maxToasts={10} position="bottom-right">  // UX-optimized limits
  <Toast type="success" message="Clean, professional notification" />
</ToastProvider>
```

#### Scrollable Dialog Patterns (2025 Standard)
```tsx
// REVOLUTIONARY SCROLLABLE DIALOG ARCHITECTURE - StrategyWizardDialog Pattern
const ScrollableDialog: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4 z-50">
      <div className="w-full max-w-5xl h-full sm:h-[95vh] flex flex-col">
        <Card className="flex flex-col bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border border-white/20 dark:border-gray-700/20 rounded-none sm:rounded-2xl shadow-2xl overflow-hidden h-full">
          
          {/* 1. FIXED HEADER - Always visible, consistent height */}
          <CardHeader className="flex-shrink-0 flex flex-row items-center justify-between pb-4 px-4 sm:px-6 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white tracking-tight">
              Dialog Title
            </h2>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </CardHeader>

          {/* 2. SCROLLABLE CONTENT AREA - Flexible height, optimized overflow */}
          <CardContent className="flex-1 flex flex-col overflow-hidden p-0">
            
            {/* Fixed UI Elements (Always Visible) */}
            <div className="flex-shrink-0 bg-gray-50 dark:bg-gray-700/50 px-4 py-4 border-b border-gray-200 dark:border-gray-600">
              {/* Important controls that should always be accessible */}
            </div>

            {/* Scrollable Dynamic Content */}
            <div className="flex-1 overflow-y-auto">
              {/* Complex forms, position lists, multi-section content */}
              <div className="p-4 space-y-4">
                {/* Dynamic content that can grow infinitely */}
              </div>
            </div>
            
            {/* 3. STICKY FOOTER - Fixed at bottom, outside scroll area */}
            <div className="flex-shrink-0 sticky bottom-0 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-700/50 p-4">
              <div className="flex items-center justify-between gap-3">
                {/* Action buttons, error messages */}
              </div>
            </div>
            
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// MOBILE OPTIMIZATION PRINCIPLES:
// ✅ Full height utilization: h-full sm:h-[95vh]
// ✅ Responsive padding: p-2 sm:p-4  
// ✅ Scrollable content prevents footer overlap
// ✅ Fixed header provides context and navigation
// ✅ Backdrop blur maintains visual hierarchy
// ✅ Sticky footer ensures action accessibility
```

#### Complex Form State Management
```tsx
// PATTERN: Multi-section state with nested objects
interface ComplexFormState {
  items: Array<{
    id: string;
    config: {
      selectionMethod: 'ATM_POINT' | 'CLOSEST_PREMIUM';
      riskManagement: {
        stopLoss: { enabled: boolean; value: number };
        targetProfit: { enabled: boolean; value: number };
      };
    };
  }>;
  globalConfig: {
    timing: { entry: string; exit: string };
    settings: { moveSlToCost: boolean };
  };
}

// STATE UPDATES: Immutable patterns with nested updates
const updateItemConfig = useCallback((itemId: string, newConfig: Partial<ItemConfig>) => {
  setItems(prev => prev.map(item => 
    item.id === itemId ? { ...item, config: { ...item.config, ...newConfig } } : item
  ));
}, []);
```

#### Design Audit Checklist
```tsx
// BEFORE COMMITTING - RUN THIS CHECKLIST:
// □ No emoji in titles, headers, or UI labels
// □ No "Revolutionary/Amazing/Stunning" marketing language  
// □ Consistent glassmorphism backdrop-blur usage
// □ Professional typography hierarchy maintained
// □ Hover effects over constant animations
// □ Functional icons, no decorative symbols
// □ Blue-gray professional color palette
// □ Content-first, information-focused layout
// □ Scrollable dialogs use fixed header + sticky footer pattern
// □ Mobile-first responsive design (p-2 sm:p-4 patterns)
// □ Complex forms use nested state management patterns
// □ JSX structure properly nested with overflow management
```

## File Structure Patterns

### Directory Organization
```
project-name/
├── CLAUDE.md                    # Project-specific guidance
├── cdk_stack/                   # Infrastructure as code
│   ├── project_stack.py        # Main stack definition
│   └── constructs/              # Reusable constructs
├── lambda_functions/            # Business logic
│   ├── function_name/           # Per-function directory
│   │   ├── lambda_function.py   # Main handler
│   │   ├── requirements.txt     # Function dependencies
│   │   └── tests/               # Function-specific tests
└── tests/                       # Integration tests
```

### File Naming Conventions
- **Python files**: `snake_case.py`
- **TypeScript files**: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- **CDK stacks**: `project_name_stack.py`
- **Lambda handlers**: `lambda_function.py` (consistent across all functions)
- **Test files**: `test_function_name.py`

## CDK & Infrastructure Patterns

### Stack Creation Standards
```python
class ProjectStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Use configuration-driven values
        config = self.node.try_get_context("environments")[environment]
        module_prefix = config["module_prefix"]
        
        # Lambda function with required patterns
        function = Function(
            self, f"{module_prefix}FunctionName",
            runtime=Runtime.PYTHON_3_11,  # Always Python 3.11
            handler="lambda_function.lambda_handler",
            code=Code.from_asset("lambda_functions/function_name"),
            function_name=f"{module_prefix}-function-name",
            log_retention=RetentionDays.ONE_WEEK,  # Use logRetention, not explicit LogGroups
            environment={
                "MODULE_PREFIX": module_prefix
            }
        )
```

### Resource Naming Pattern
```python
# Construct IDs: {module_prefix}{ResourceType}{Description}
construct_id = f"{module_prefix}DynamoDBTable"

# Resource names: {module-prefix}-{resource-type}-{description}
resource_name = f"{module_prefix}-dynamodb-table"

# Export names: {module-prefix}-{ResourceType}
export_name = f"{module_prefix}-UserPoolId"
```

## Testing Standards

### Test Structure Pattern
```python
import pytest
from unittest.mock import MagicMock, patch
from lambda_functions.function_name.lambda_function import lambda_handler

class TestFunctionName:
    """Test class for function_name Lambda function."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.context = MagicMock()
        
    def test_successful_operation(self):
        """Test successful operation with valid inputs."""
        # Arrange
        event = {
            "key": "value"
        }
        
        # Act
        result = lambda_handler(event, self.context)
        
        # Assert
        assert result["statusCode"] == 200
        assert "expected_key" in result["body"]
        
    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        # Arrange
        event = {}  # Invalid event
        
        # Act & Assert
        with pytest.raises(KeyError):
            lambda_handler(event, self.context)
```

### Test Data Patterns
```python
# Use realistic test data
VALID_OPTION_CHAIN = {
    "symbol": "NIFTY",
    "expiry": "2024-01-25",
    "strike": 21000,
    "option_type": "CE"
}

# Test edge cases explicitly
EDGE_CASES = [
    {"name": "weekend_execution", "data": {"day": "Saturday"}},
    {"name": "market_closed", "data": {"time": "16:00"}},
    {"name": "invalid_strike", "data": {"strike": -1000}}
]
```

## Documentation Standards

### Code Comments
```python
def calculate_next_minute_wait_seconds(current_ist: datetime) -> int:
    """
    Calculate exact seconds to hit next 0-second boundary.
    
    This function implements the revolutionary 0-second precision timing
    algorithm that eliminates EventBridge delays.
    
    Args:
        current_ist: Current IST datetime
        
    Returns:
        Seconds to wait (minimum 1) for next minute boundary
    """
    current_second = current_ist.second
    seconds_remaining = 60 - current_second
    return max(1, seconds_remaining)  # Prevent 0-second wait
```

### CLAUDE.md Structure
```markdown
# Project Name

Brief project description and current status.

## Architecture Overview
High-level architecture explanation.

## Development Patterns
Project-specific patterns and conventions.

## Deployment Guide
Step-by-step deployment instructions.

### Frontend Testing Standards (TypeScript/React)

#### Jest Configuration Pattern
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/test/**/*',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    'src/utils/strategy/': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
  },
};
```

#### Test Structure Pattern
```typescript
// Component tests
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  const user = userEvent.setup();
  
  it('should render with required props', () => {
    render(<ComponentName prop="value" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
  
  it('should handle user interactions', async () => {
    const mockHandler = jest.fn();
    render(<ComponentName onClick={mockHandler} />);
    
    await user.click(screen.getByRole('button'));
    expect(mockHandler).toHaveBeenCalledTimes(1);
  });
});
```

#### Mock Patterns
```typescript
// API mocks
export const mockStrategyService = {
  createStrategy: jest.fn<Promise<ApiResponse>, [string, StrategyData]>(),
  getStrategy: jest.fn<Promise<ApiResponse>, [string]>(),
};

// Test utilities
export const renderWithRouter = (ui: ReactElement, options?: RenderOptions) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <BrowserRouter>{children}</BrowserRouter>
  );
  return render(ui, { wrapper: Wrapper, ...options });
};
```

## Testing Strategy
Testing approach and execution.

## Monitoring & Operations
Operational procedures and monitoring setup.
```

## Git & Version Control

### Commit Message Format
```
type: Brief description of changes

Detailed explanation if necessary, including:
- What was changed and why
- Any breaking changes
- Related issue numbers

Examples:
feat: Revolutionary 0-second precision timing system with Standard Step Functions
fix: Resolve LogGroup deployment conflicts in CDK stack
docs: Update architecture patterns in CLAUDE.md
test: Add comprehensive GSI2 optimization validation
```

### Branch Naming
- **Feature branches**: `feature/description-of-feature`
- **Bug fixes**: `fix/description-of-fix`
- **Documentation**: `docs/description-of-update`
- **Main branch**: `main` (protected)

## Error Handling Patterns

### Lambda Function Error Handling
```python
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Standard Lambda handler with error handling."""
    try:
        # Log incoming event
        logger.info(f"Processing event: {json.dumps(event)}")
        
        # Validate inputs
        if not validate_input(event):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid input"})
            }
        
        # Process request
        result = process_request(event)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
```

## Performance & Optimization Standards

### DynamoDB Query Patterns
```python
# Use GSI2 optimization pattern
def get_strategy_data(user_id: str, strategy_id: str) -> dict:
    """Get strategy data with optimized single query."""
    response = dynamodb.query(
        IndexName='GSI2',
        KeyConditionExpression=Key('GSI2PK').eq(f"USER#{user_id}") & 
                             Key('GSI2SK').begins_with(f"STRATEGY#{strategy_id}")
    )
    return response['Items']
```

### Step Functions State Machine Patterns
```python
# Use precise wait calculations
{
    "Type": "Wait",
    "SecondsPath": "$.wait_seconds",  # Dynamic wait from Lambda
    "Next": "ExecuteStrategy"
}
```

This style guide ensures consistency, quality, and maintainability across the entire project while supporting the revolutionary features that set this platform apart from competitors.