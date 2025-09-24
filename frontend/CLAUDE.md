# Frontend - CLAUDE.md

This file provides **frontend-specific guidance** for the Quantleap Analytics trading platform.

**📋 Shared Context**: Root `/CLAUDE.md` contains shared AWS configuration, deployment patterns, and enterprise standards
**🏗️ Architecture**: Complex architectural decisions managed by `/.claude/agents/architecture_agent.md`

## Current Environment Configuration (September 11, 2025)

### ✅ Multi-API Architecture Deployment
**Status**: ✅ Updated with both deployed stack endpoints

#### **API Endpoints**:
- **User Authentication & Broker Management**: `https://fx43f0dnr4.execute-api.ap-south-1.amazonaws.com/dev/`
- **Options Trading Platform**: `https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev/`

#### **Environment Variables** (`.env`):
```env
REACT_APP_ENVIRONMENT=dev
REACT_APP_API_URL_DEV=https://fx43f0dnr4.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_OPTIONS_API_URL_DEV=https://vrd3rrtyx4.execute-api.ap-south-1.amazonaws.com/dev
REACT_APP_DEBUG=true
REACT_APP_AUTH_STACK_NAME=ql-algo-trading-dev-auth-broker-stack
REACT_APP_OPTIONS_STACK_NAME=ql-algo-trading-dev-options-trading-stack
```

#### **Development Status**:
- **Frontend Server**: Running at `http://localhost:3000`
- **Hot Reload**: Active with updated environment variables
- **TypeScript**: Clean compilation with comprehensive type safety
- **API Integration**: Dual API architecture configured and ready

## Development Standards

### Layout Pattern (MANDATORY)
All React pages MUST follow this exact pattern for consistency:

```tsx
const PageComponent: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Page Title</h1>
      
      {/* Content sections with consistent spacing */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Stat cards or content blocks */}
      </div>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          {/* Header section */}
        </div>
        <div className="p-6">
          {/* Main content */}
        </div>
      </div>
    </div>
  );
};
```

### Critical Layout Rules
1. **Root Container**: ALWAYS use `<div className="space-y-6">` - never add width constraints
2. **Page Titles**: ALWAYS use `text-2xl font-bold` - never text-3xl
3. **Section Spacing**: Use `space-y-6` between major sections
4. **Cards**: Use `bg-white dark:bg-gray-800 rounded-lg shadow`
5. **No Width Constraints**: Layout component handles responsive padding

### Design System Components

#### Typography
- **Page Headers**: `text-2xl font-bold text-gray-900 dark:text-white`
- **Section Headers**: `text-lg font-semibold text-gray-900 dark:text-white`
- **Body Text**: `text-gray-600 dark:text-gray-300`
- **Labels**: `text-sm font-medium text-gray-700 dark:text-gray-200`

#### Form Elements
- **Input Background**: `bg-white dark:bg-gray-700`
- **Input Borders**: `border-gray-300 dark:border-gray-600`
- **Input Text**: `text-gray-900 dark:text-white`
- **Placeholders**: `placeholder-gray-500 dark:placeholder-gray-400`
- **Focus States**: `focus:ring-2 focus:ring-blue-500 focus:border-blue-500`

#### Interactive Elements
- **Primary Buttons**: `bg-blue-600 hover:bg-blue-700 text-white`
- **Links**: `text-blue-600 dark:text-blue-400 hover:text-blue-500 dark:hover:text-blue-300`
- **Disabled States**: `disabled:bg-blue-300 dark:disabled:bg-blue-800`

#### Cards and Containers
- **Card Background**: `bg-white dark:bg-gray-800`
- **Card Borders**: `border border-gray-200 dark:border-gray-700`
- **Card Shadows**: `shadow` or `shadow-lg`
- **Card Padding**: `p-6` for content areas

#### Status and Feedback
- **Success**: `bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200`
- **Error**: `bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200`
- **Warning**: `bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200`
- **Info**: `bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200`

#### Toast Notifications (New)
- **Container Architecture**: Fixed positioning with container-managed stacking
- **Usage Pattern**: `<ToastProvider maxToasts={10} position="bottom-right">`
- **Individual Toasts**: Use `relative` positioning within container
- **Proper Spacing**: `gap-2` for clean vertical stacking
- **No Overlap**: Resolved positioning conflicts with architectural fix

## Recent Updates

### Toast Notification System (2025-09-09)
- ✅ Fixed overlapping toast notifications with improved positioning architecture
- ✅ Changed from individual `fixed` positioning to container-managed `relative` positioning
- ✅ Increased maxToasts limit from 5 to 10 for better user experience
- ✅ Implemented proper gap spacing with `gap-2` for clean toast stacking
- ✅ Maintained slide-in animations and auto-dismiss functionality

### Auth Pages Styling (2025-08-30)
- ✅ Standardized all authentication forms with project design system
- ✅ Added comprehensive dark mode support across all auth components
- ✅ Replaced custom gradients with consistent gray backgrounds
- ✅ Updated form inputs, labels, and interactive elements for dark mode
- ✅ Used consistent Turtle icon from main app in AuthPage header

### Layout Standardization (2025-08-30)
- ✅ Updated BrokersPage to match algo-platform layout pattern
- ✅ Standardized Dashboard heading size (text-2xl)
- ✅ Updated placeholder routes with consistent layout containers
- ✅ Removed arbitrary width constraints (`max-w-7xl mx-auto`)

## Component Architecture

### Authentication Components
- **AuthPage**: Main auth container with consistent styling
- **LoginForm**: Email/phone login with dark mode support
- **RegisterForm**: User registration with Indian market validation
- **ForgotPasswordForm**: Password reset flow
- **ResetPasswordForm**: Password reset confirmation
- **EmailVerificationForm**: Email verification process

### Layout Components
- **Layout**: Main layout with sidebar and responsive padding
- **Header**: Top navigation with user menu
- **Sidebar**: Navigation menu with proper mobile support

### Page Components
- **Dashboard**: Welcome page with profile summary and stats
- **BrokersPage**: Broker account management interface

## Development Commands

### Development Server
```bash
cd frontend
npm start
```

### Build and Deploy
```bash
npm run build
```

### Testing Infrastructure ⭐ NEW
```bash
# Interactive testing
npm test

# Comprehensive test suites
npm run test:all          # Run all test categories
npm run test:utils        # Test utility functions  
npm run test:services     # Test API services
npm run test:components   # Test React components
npm run test:integration  # Test end-to-end workflows

# Coverage and reporting
npm run test:coverage     # Generate coverage reports
npm run test:ci          # CI/CD optimized testing
npm run test:verbose     # Detailed test output

# Development testing
npm run test:watch       # Watch mode for development
npm run test:update      # Update test snapshots
```

#### Test Configuration
- **Jest**: Industry-standard configuration with 80-95% coverage thresholds
- **React Testing Library**: Component testing with user interaction simulation
- **Coverage Reports**: HTML, LCOV, and JSON formats in `coverage/` directory
- **Test Files**: Located in `src/test/` with organized suites by category

## Common Patterns

### Error Handling
Always use consistent error message styling:
```tsx
{error && (
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
    <div className="flex items-center gap-2">
      <XCircle className="h-5 w-5 text-red-600" />
      <span className="text-red-800 dark:text-red-200">{error}</span>
    </div>
  </div>
)}
```

### Loading States
Use consistent loading indicators:
```tsx
{loading && (
  <div className="flex items-center justify-center py-12">
    <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
    <span className="ml-2 text-gray-600 dark:text-gray-400">Loading...</span>
  </div>
)}
```

### Table Styling
Use consistent table styling across all data tables:
```tsx
<table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
  <thead className="bg-gray-50 dark:bg-gray-700">
    <tr>
      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
        Header
      </th>
    </tr>
  </thead>
  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
        Content
      </td>
    </tr>
  </tbody>
</table>
```

## Integration Notes

### API Integration
- All API calls use axios with interceptors for auth headers
- Consistent error handling across all services
- Environment-based API URL configuration

### State Management
- AuthContext for user authentication state
- Component-level state for page-specific data
- Consistent loading and error state patterns

## Recent Updates

### September 12, 2025 - Product Type System & UI Consistency Enhancement
- ✅ **Complete Product Type System**: Comprehensive MIS/NRML validation with business rules
- ✅ **UI Components**: GlobalIndexSelector and PositionsSection components for better architecture
- ✅ **Business Logic Validation**: ProductTypeValidation utility with 31 comprehensive tests
- ✅ **Position-Level Integration**: Product type badges displayed alongside index and expiry
- ✅ **Component Architecture**: Improved StrategyWizardDialog with row-based layout
- ✅ **Type Safety**: Enhanced TypeScript interfaces for product type prop drilling
- ✅ **Default Configuration**: Changed system default from MIS to NRML as requested

### UI Consistency Enhancement (September 12, 2025)
- ✅ **Connected Toggle Pattern**: Standardized trading type (INTRADAY/POSITIONAL) toggle to match MIS/NRML styling
- ✅ **Design System Compliance**: Updated StrategyConfiguration component with connected button group pattern
- ✅ **Consistent Styling**: Both toggles now use `flex rounded-lg overflow-hidden border` container with `border-l` separators
- ✅ **2025 Design Standards**: Maintained minimalist design principles with unified toggle appearances
- ✅ **Cross-Component Harmony**: Achieved visual consistency across all strategy configuration interfaces

### September 11, 2025 - Testing Infrastructure & ATM_POINTS Migration  
- ✅ **Comprehensive Testing Suite**: Added Jest configuration with 4 test categories and 10 test scripts
- ✅ **Strike Selection Enhancement**: Migrated ATM_POINT to ATM_POINTS with bidirectional transformation
- ✅ **Test Coverage**: 80-95% coverage thresholds with HTML/LCOV reporting
- ✅ **Type Safety**: Complete TypeScript integration with strategy type system
- ✅ **CI/CD Integration**: GitHub Actions workflow and jest-junit reporting
- ✅ **Repository Security**: Enhanced .gitignore with frontend-specific patterns

### Toast Notification System (2025-09-09)
- ✅ Fixed overlapping toast notifications with improved positioning architecture
- ✅ Changed from individual `fixed` positioning to container-managed `relative` positioning
- ✅ Increased maxToasts limit from 5 to 10 for better user experience
- ✅ Implemented proper gap spacing with `gap-2` for clean toast stacking
- ✅ Maintained slide-in animations and auto-dismiss functionality

### Auth Pages Styling (2025-08-30)
- ✅ Standardized all authentication forms with project design system
- ✅ Added comprehensive dark mode support across all auth components
- ✅ Replaced custom gradients with consistent gray backgrounds
- ✅ Updated form inputs, labels, and interactive elements for dark mode
- ✅ Used consistent Turtle icon from main app in AuthPage header

## Future Development Guidelines

When creating new pages or components:
1. **ALWAYS** start with the standard layout pattern
2. Use the established design system components
3. Implement full dark mode support from the beginning
4. Follow existing API service patterns
5. Include proper error handling and loading states
6. Test on both desktop and mobile viewports
7. **NEW**: Write comprehensive tests using Jest and React Testing Library