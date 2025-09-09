---
created: 2025-09-05T19:46:11Z
last_updated: 2025-09-08T17:56:25Z
version: 1.2
author: Claude Code PM System
---

# Project Structure

## Root Directory Organization

### Core Configuration Files
```
aws-learning-examples/
├── CLAUDE.md                              # Master project guidance & dev rules
├── README.md                              # Project overview & quick start
├── .gitignore                             # Git exclusions
├── aws-learning-examples.iml              # IntelliJ project file
└── docs/                                  # Centralized documentation
    ├── development/                       # Development & deployment guides
    │   ├── LOGGING.md                     # Logging standards & practices
    │   └── UI_ENHANCEMENT_ROADMAP.md      # Frontend development roadmap
    ├── requirements/                      # Product & business docs
    │   └── OPTIONS_STRATEGY_REQUIREMENTS.md  # Detailed requirements doc
    └── architecture/                      # High-level architecture docs
        └── REVOLUTIONARY_FEATURES_SUMMARY.md  # Platform capabilities summary
```

### Project Management & Tooling
```
├── .claude/                               # Claude Code PM system (78+ files)
│   ├── CLAUDE.md                         # Development philosophy & rules
│   ├── agents/                           # Specialized sub-agents
│   ├── commands/                         # PM commands & workflows
│   ├── context/                          # Project context files (this directory)
│   ├── epics/                            # Epic management (unused)
│   ├── prds/                             # Product requirements (unused)
│   ├── rules/                            # PM system rules & patterns
│   └── scripts/                          # Automation scripts
```

## Multi-Project Architecture

### Primary Development Projects
```
├── options-strategy-platform/             # Revolutionary trading platform
│   ├── CLAUDE.md                         # Platform-specific guidance
│   ├── README.md                         # Module overview & quick start
│   ├── cdk_stack/                        # Infrastructure as code
│   ├── lambda_functions/                 # Core business logic
│   │   └── option_baskets/               # Trading execution functions
│   │       ├── single_strategy_executor.py      # Individual strategy processing
│   │       ├── strategy_scheduler.py           # SQS-to-Step Function launcher
│   │       ├── step_function_launcher.py       # Batch processing launcher
│   │       └── user_strategy_executor.py       # User-level parallel execution
│   ├── step_functions/                   # Workflow definitions (JSON)
│   │   ├── single_strategy_express_execution.json    # Express timing workflows
│   │   ├── batch_strategy_execution_definition.json  # Batch processing
│   │   └── user_execution_definition.json            # User-level orchestration
│   ├── tests/                            # Comprehensive test suite
│   │   └── options_strategies/           # Trading-specific tests
│   ├── test-venv/                        # Isolated testing environment
│   ├── docs/                             # Module documentation
│   │   ├── design/                       # Technical design documents
│   │   │   ├── OPTIONS_TRADING_DESIGN.md             # Core platform architecture
│   │   │   └── COMPLETE_LOT_MULTIPLIER_FLOW_REFERENCE.md  # Detailed flow docs
│   │   ├── testing/                      # Testing documentation
│   │   │   ├── TESTING_GUIDE.md          # Comprehensive testing framework
│   │   │   ├── COMPLETE_FLOW_TESTING_GUIDE.md  # End-to-end validation
│   │   │   └── README_E2E_TESTING.md     # E2E testing setup
│   │   └── architecture/                 # Module architecture
│   │       └── lightweight-architecture.md  # Revolutionary breakthrough docs
│   └── validation_results.json          # Performance benchmarking results
```

```
├── user-auth-broker-management/           # Authentication & broker accounts
│   ├── CLAUDE.md                         # Auth-specific patterns
│   ├── cdk_stack/                        # User & broker infrastructure
│   └── lambda_functions/                 # Auth & broker handlers
```

```
├── event-bridge-stepfunction-lambda/      # Learning project (EventBridge)
│   ├── CLAUDE.md                         # Basic serverless patterns
│   ├── cdk_stack/                        # Simple event-driven architecture
│   └── lambda_functions/                 # Event processing functions
```

### Frontend Applications
```
├── frontend/                             # Main React/TypeScript frontend
│   ├── package.json                      # Dependencies & scripts
│   ├── src/                              # React application source
│   └── public/                           # Static assets
```

```
├── frontend-amplify/                     # Experimental Amplify version
│   └── package.json                      # Amplify-specific dependencies
```

### Shared Resources
```
├── shared_config/                        # Cross-project configuration
├── shared_scripts/                       # Deployment & utility scripts
├── shared_utils/                         # Common utilities & patterns
└── .venv/                               # Python virtual environment
```

## Key Naming Patterns

### File Organization Conventions
- **CLAUDE.md files**: Project guidance at each level (hierarchical)
- **cdk_stack/** directories: Infrastructure code organization
- **lambda_functions/** directories: Business logic separation
- **tests/** directories: Comprehensive testing structure

### Resource Naming Standards
- **Module prefixes**: `ql-algo-trading` for options platform
- **Environment suffixes**: `-dev`, `-staging`, `-prod`
- **Function naming**: Descriptive with consistent patterns
- **Stack naming**: `{project}-{env}-{module}-stack`

## Directory Depth & Organization

### Shallow Root Structure
- **5 main projects** at root level for easy navigation
- **3 shared resource** directories for common patterns
- **Clear separation** between infrastructure and application code

### Deep Module Structure
- **3-4 levels deep** within each project for logical organization
- **Consistent patterns** across all projects for familiarity
- **Test co-location** near implementation code

## Integration Points

### Cross-Project Dependencies
- **Shared config** used by all CDK stacks
- **Common utilities** imported across Lambda functions
- **Consistent deployment** patterns via shared scripts

### AWS Resource Sharing
- **Cross-stack references** between auth and options platforms
- **Shared API Gateway** with different endpoint routes
- **Common monitoring** and alerting infrastructure

## Development Environment Setup

### IDE Configuration
- **IntelliJ IDEA** project file for unified development
- **Multiple Python** virtual environments for isolation
- **Node.js projects** with separate package.json files

### Build & Deployment
- **Individual deploy.sh** scripts per project
- **Profile-based** AWS deployment validation
- **Environment-specific** configuration management

## Update History
- 2025-09-08: Major PM system integration - 78+ new files in .claude/ directory, expanded options-strategy-platform with new Lambda functions and Step Function definitions
- 2025-09-08: Complete documentation reorganization - centralized root docs, standardized module structure, eliminated duplicates, showcased revolutionary features